#!/usr/bin/env python3
"""Validate filing-review manifest, evidence ledger, and findings.

Usage:
  python validate_review_artifacts.py \
    --manifest manifest.json \
    --ledger evidence-ledger.json \
    --findings findings.jsonl

JSON Schema validation is used when jsonschema is installed. Core cross-file and
status invariants are always checked with the standard library.

Exit code is driven by errors only. Warnings (possible duplicate signatures,
CONFIRMED numeric findings not linked to declared authority sources) are
reported in the output JSON but do not change the exit code.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import jsonschema
except Exception:  # pragma: no cover - optional dependency
    jsonschema = None

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "assets"
VALID_EVIDENCE_STATUS = {"CONFIRMED", "CANDIDATE", "PASS", "UNVERIFIABLE", "NOT_IN_SCOPE"}
VALID_COVERAGE_STATUS = {"COMPLETE", "PARTIAL", "NOT_RUN", "UNVERIFIABLE", "NOT_IN_SCOPE"}


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_number}: JSONL record must be an object")
            records.append(item)
    return records


def schema_errors(instance: Any, schema_path: Path) -> list[str]:
    if jsonschema is None:
        return []
    schema = read_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{schema_path.name}: {'/'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
        for error in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path))
    ]


def duplicate_ids(items: list[dict[str, Any]], label: str) -> list[str]:
    counts = Counter(item.get("id") for item in items if item.get("id"))
    return [f"duplicate {label} id: {item_id} ({count}x)" for item_id, count in counts.items() if count > 1]


def validate(manifest: dict[str, Any], ledger: dict[str, Any], findings: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    errors.extend(schema_errors(manifest, SCHEMA_DIR / "review-manifest.schema.json"))
    errors.extend(schema_errors(ledger, SCHEMA_DIR / "evidence-ledger.schema.json"))
    for finding in findings:
        errors.extend(schema_errors(finding, SCHEMA_DIR / "finding.schema.json"))

    claims = ledger.get("claims", [])
    sources = ledger.get("sources", [])
    evidence = ledger.get("evidence", [])
    errors.extend(duplicate_ids(claims, "claim"))
    errors.extend(duplicate_ids(sources, "source"))
    errors.extend(duplicate_ids(evidence, "evidence"))
    errors.extend(duplicate_ids(findings, "finding"))

    claim_ids = {item.get("id") for item in claims}
    source_ids = {item.get("id") for item in sources}
    evidence_ids = {item.get("id") for item in evidence}
    document_ids = {
        item.get("id")
        for item in manifest.get("scope", {}).get("documents", [])
        if item.get("id")
    }

    for claim in claims:
        claim_id = claim.get("id", "<missing>")
        for source_id in claim.get("source_ids", []):
            if source_id not in source_ids:
                errors.append(f"claim {claim_id} references missing source {source_id}")
        for evidence_id in claim.get("evidence_ids", []):
            if evidence_id not in evidence_ids:
                errors.append(f"claim {claim_id} references missing evidence {evidence_id}")
        if claim.get("status") == "CONFIRMED" and not claim.get("evidence_ids"):
            errors.append(f"claim {claim_id} is CONFIRMED but has no evidence_ids")
        if claim.get("status") == "UNVERIFIABLE" and not claim.get("unverifiable_reason"):
            errors.append(f"claim {claim_id} is UNVERIFIABLE but has no unverifiable_reason")

    for item in evidence:
        evidence_id = item.get("id", "<missing>")
        if item.get("claim_id") not in claim_ids:
            errors.append(f"evidence {evidence_id} references missing claim {item.get('claim_id')}")
        if item.get("source_id") not in source_ids:
            errors.append(f"evidence {evidence_id} references missing source {item.get('source_id')}")

    for finding in findings:
        finding_id = finding.get("id", "<missing>")
        if finding.get("document_id") not in document_ids:
            errors.append(f"finding {finding_id} references unknown document_id {finding.get('document_id')}")
        for evidence_id in finding.get("evidence_ids", []):
            if evidence_id not in evidence_ids:
                errors.append(f"finding {finding_id} references missing evidence {evidence_id}")
        status = finding.get("evidence_status")
        impact = finding.get("impact")
        if status == "CONFIRMED" and not finding.get("evidence_ids"):
            errors.append(f"finding {finding_id} is CONFIRMED but has no evidence_ids")
        if status == "CONFIRMED" and impact == "A" and len(finding.get("counter_arguments", [])) < 3:
            errors.append(f"finding {finding_id} is A/CONFIRMED but has fewer than 3 counter_arguments")
        if status == "UNVERIFIABLE" and not finding.get("unverifiable_reason"):
            errors.append(f"finding {finding_id} is UNVERIFIABLE but has no unverifiable_reason")
        if status not in VALID_EVIDENCE_STATUS:
            errors.append(f"finding {finding_id} has invalid evidence_status {status}")
        if finding.get("coverage_status") not in VALID_COVERAGE_STATUS:
            errors.append(f"finding {finding_id} has invalid coverage_status {finding.get('coverage_status')}")

    for coverage in manifest.get("coverage", []):
        if coverage.get("status") not in VALID_COVERAGE_STATUS:
            errors.append(f"coverage {coverage.get('item_id', '<missing>')} has invalid status {coverage.get('status')}")
        if coverage.get("status") in {"PARTIAL", "NOT_RUN", "UNVERIFIABLE", "NOT_IN_SCOPE"} and not coverage.get("reason"):
            errors.append(f"coverage {coverage.get('item_id', '<missing>')} requires a reason")

    warnings: list[str] = []

    # 同签名未归并提示：finding_type + root_cause 相同且 >1 条
    signature_counts = Counter(
        (f.get("finding_type"), f.get("root_cause"))
        for f in findings
        if f.get("root_cause")
    )
    for (finding_type, root_cause), count in signature_counts.items():
        if count > 1:
            ids = [
                f.get("id")
                for f in findings
                if f.get("finding_type") == finding_type and f.get("root_cause") == root_cause
            ]
            warnings.append(
                f"possible duplicate signature ({finding_type}/{root_cause}): "
                f"{count} findings {ids}; confirm merged or linked via related_locations"
            )

    # 权威来源挂载检查：CONFIRMED 且关联 numeric claim 的 finding，
    # 至少一条证据应来自 manifest 已声明的 authority_baseline 来源
    baseline = manifest.get("scope", {}).get("authority_baseline", [])
    for item in baseline:
        if isinstance(item, str):
            warnings.append(
                f"authority_baseline entry {item!r} uses legacy string format; "
                f"migrate to {{data_type, source_ref, note}} object format "
                f"(source_ref should be an SRC- ID from the evidence ledger); "
                f"legacy entries are ignored in the authority-source mount check below"
            )
    authority_sources = {
        item.get("source_ref")
        for item in baseline
        if isinstance(item, dict) and str(item.get("source_ref", "")).startswith("SRC-")
    }
    if authority_sources:
        claim_type_by_id = {c.get("id"): c.get("claim_type") for c in claims}
        evidence_by_id = {e.get("id"): e for e in evidence}
        for finding in findings:
            if finding.get("evidence_status") != "CONFIRMED":
                continue
            linked = [evidence_by_id.get(eid) for eid in finding.get("evidence_ids", [])]
            linked = [e for e in linked if e]
            is_numeric = any(claim_type_by_id.get(e.get("claim_id")) == "numeric" for e in linked)
            if not is_numeric:
                continue
            if not any(e.get("source_id") in authority_sources for e in linked):
                warnings.append(
                    f"finding {finding.get('id')} is CONFIRMED numeric but has no "
                    f"evidence from declared authority_baseline sources"
                )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--findings", required=True, help="findings.jsonl")
    args = parser.parse_args()

    try:
        manifest = read_json(Path(args.manifest))
        ledger = read_json(Path(args.ledger))
        findings = read_jsonl(Path(args.findings))
        errors, warnings = validate(manifest, ledger, findings)
    except Exception as exc:
        print(f"VALIDATION ERROR: {exc}", file=sys.stderr)
        return 2

    if errors:
        print(json.dumps({"status": "FAIL", "error_count": len(errors), "errors": errors, "warnings": warnings}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps({
        "status": "PASS",
        "claims": len(ledger.get("claims", [])),
        "sources": len(ledger.get("sources", [])),
        "evidence": len(ledger.get("evidence", [])),
        "findings": len(findings),
        "warnings": warnings,
        "schema_engine": "jsonschema" if jsonschema is not None else "core-checks-only",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
