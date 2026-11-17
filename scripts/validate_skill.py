#!/usr/bin/env python3
"""Dependency-free structural validation for public contributions."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "SKILL.md",
    "README.md",
    "CHANGELOG.md",
    "_skillhub_meta.json",
    "references",
    "assets",
    "scripts",
]
MARKDOWN_LINK = re.compile(r"\]\(([^)\n]+)\)")
FORBIDDEN_PATTERNS = {
    "本机用户目录": re.compile(r"/Users/[^/\s]+/"),
    "OneDrive 个人路径": re.compile(r"OneDrive-个人"),
    "微信标识": re.compile(r"wxid_[A-Za-z0-9_-]+"),
    "GitHub Token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "OpenAI 风格密钥": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "AWS Access Key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "私钥": re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"),
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_required_paths() -> None:
    missing = [name for name in REQUIRED if not (ROOT / name).exists()]
    if missing:
        fail("缺少必要文件或目录: " + ", ".join(missing))


def validate_front_matter() -> None:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail("SKILL.md 必须以 YAML front matter 开头")
    try:
        _, front_matter, _ = text.split("---", 2)
    except ValueError:
        fail("SKILL.md front matter 未闭合")
    for key in ("name:", "description:"):
        if not re.search(rf"(?m)^{re.escape(key)}", front_matter):
            fail(f"SKILL.md front matter 缺少 {key}")


def validate_json() -> None:
    for path in sorted(ROOT.rglob("*.json")):
        if ".git" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"JSON 无效: {path.relative_to(ROOT)}: {exc}")


def validate_python() -> None:
    for path in sorted(ROOT.rglob("*.py")):
        if ".git" in path.parts:
            continue
        try:
            compile(path.read_bytes(), str(path), "exec")
        except Exception as exc:
            fail(f"Python 语法错误: {path.relative_to(ROOT)}: {exc}")


def validate_markdown_links() -> None:
    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().strip("<>").split()[0]
            if not target or any(ch in target for ch in "[]{}`"):
                continue
            if target.startswith(
                ("http://", "https://", "mailto:", "#", "codex://", "plugin://")
            ):
                continue
            target = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not target or target.startswith("/"):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                fail(f"Markdown 链接越出仓库: {path.relative_to(ROOT)} -> {raw_target}")
            if not resolved.exists():
                fail(f"Markdown 链接不存在: {path.relative_to(ROOT)} -> {raw_target}")


def validate_sensitive_content() -> None:
    own_path = Path(__file__).resolve()
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or path.resolve() == own_path:
            continue
        if path.suffix.lower() not in {
            ".md", ".py", ".json", ".yaml", ".yml", ".txt", ".csv", ".toml", ".ini", ""
        }:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(text):
                fail(f"发现{label}: {path.relative_to(ROOT)}")


def main() -> None:
    validate_required_paths()
    validate_front_matter()
    validate_json()
    validate_python()
    validate_markdown_links()
    validate_sensitive_content()
    print("Skill contribution validation passed.")


if __name__ == "__main__":
    main()
