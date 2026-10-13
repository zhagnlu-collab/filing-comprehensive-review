# 事实与证据台账

> 本文件统一 claim、source、evidence 和 finding 的数据结构。所有脚本、子代理、问题清单和 Word 批注应使用同一套 ID、状态和引用关系，避免"报告里是一套、批注里是另一套"。

## 一、四类对象

| 对象 | ID 前缀 | 作用 |
|---|---|---|
| Claim | `CLM-` | 待核事实、数据点、法规判断或业务主张 |
| Source | `SRC-` | 底稿、申报文件、法规、公告或外部来源 |
| Evidence | `EVD-` | 某个来源对某个 claim 的支持、反驳或补充说明 |
| Finding | `FND-` | 进入问题清单的异常、缺口或留痕结论 |

建议文件：

- `manifest.json`：范围、角色、版本和覆盖状态；
- `evidence-ledger.json`：`claims`、`sources`、`evidence` 三个数组；
- `findings.jsonl`：每行一个 finding；
- `coverage.csv`：表格、数据点、章节和来源的覆盖状态。

## 二、Claim 数据结构

```json
{
  "id": "CLM-0001",
  "claim_type": "numeric",
  "statement": "2026H1 营业收入为 207,396.73 万元",
  "entity": "标的公司",
  "metric": "营业收入",
  "period": "2026H1",
  "scope": "合并口径",
  "value": 207396.73,
  "unit": "万元",
  "currency": "CNY",
  "status": "CONFIRMED",
  "location": "问题六/主要经营数据/正文第一段",
  "source_ids": ["SRC-0001"],
  "evidence_ids": ["EVD-0001", "EVD-0002"],
  "note": ""
}
```

`claim_type` 取值：

- `numeric`：金额、数量、比例、日期等可核数据；
- `legal`：法规、监管规则、案号、合规结论；
- `business`：客户、供应商、业务模式、合同和交易事实；
- `forecast`：预测、估值假设和敏感性；
- `forward_looking`：未来计划、承诺和前瞻性陈述；
- `opinion`：专业意见或判断；
- `format`：名称、定义、单位、标点和体例。

不同 claim 类型的最低证据要求不同：

| 类型 | 最低验证方式 |
|---|---|
| numeric | 公式复算、底稿穿透或权威数据对碰 |
| legal | 法规原文、适用主体、期间和现行有效性 |
| business | 项目底稿、合同、访谈、工商或公开披露 |
| forecast | 模型底稿、假设来源、计算逻辑和敏感性 |
| forward_looking | 与已披露计划、风险因素和假设一致 |
| opinion | 不要求客观真假，但不得与客观事实冲突 |
| format | 全文一致性和项目统一口径 |

## 三、Source 数据结构

```json
{
  "id": "SRC-0001",
  "source_type": "working_paper",
  "tier": "AUTHORITY",
  "title": "2026H1 审定合并利润表",
  "publisher": "会计师事务所",
  "file_or_url": "审定报表.xlsx",
  "locator": "合并利润表!D12",
  "publish_date": "2026-08-20",
  "access_date": "2026-09-25",
  "sha256": "",
  "language": "zh-CN",
  "independent": true,
  "note": ""
}
```

`source_type` 取值：

- `working_paper`：TB、审计报告、评估说明、法律意见书、Excel 计算底稿；
- `filing`：主文件或其明确组成部分；
- `comparison`：其他申报文件；
- `regulation`：法律法规和监管规则；
- `official`：政府、交易所、法院、公司官方公告；
- `professional`：审计、评估、法律、券商或行业协会；
- `media`：可信媒体；
- `other`：搜索摘要、聚合页或无来源转述。

来源规则：

1. 优先直接内容页，不使用搜索摘要、列表页或首页单独支撑事实。
2. 外部来源必须记录发布日期和访问日期；不确定时写 `null` 并说明原因。
3. 同一事实存在多来源时，不按数量机械投票，先比较主体、期间、口径和来源独立性。
4. 来源重复转载不能视为独立佐证。
5. 来源冲突时保留全部来源，finding 标记为 `UNVERIFIABLE` 或交项目组决策，不自行取舍。

## 四、Evidence 数据结构

```json
{
  "id": "EVD-0001",
  "claim_id": "CLM-0001",
  "source_id": "SRC-0001",
  "relation": "support",
  "excerpt": "营业收入 2,073,967,319.27",
  "locator": "合并利润表!D12",
  "independent": true,
  "status": "CONFIRMED",
  "note": "元口径，折算为 207,396.73 万元"
}
```

`relation` 取值：

- `support`：支持 claim；
- `refute`：反驳 claim；
- `context`：补充口径、背景或限制，不直接支持或反驳；
- `duplicate`：转载或非独立证据。

`status` 取值与主流程一致：`CONFIRMED / CANDIDATE / PASS / UNVERIFIABLE / NOT_IN_SCOPE`。

## 五、Finding 数据结构

```json
{
  "id": "FND-0001",
  "impact": "A",
  "evidence_status": "CONFIRMED",
  "finding_type": "跨文件数据不一致",
  "title": "同一期间归母净利润在两份文件中不一致",
  "description": "主文件采用审定值，对照文件仍沿用旧值。",
  "document_id": "M1",
  "location": "问题九/（三）主要合营联营企业经营情况/表后正文",
  "original_text": "归母净利润为 20,717.86 万元",
  "expected_value": "21,008.43 万元",
  "actual_value": "20,717.86 万元",
  "difference": "-290.57 万元",
  "formula_or_evidence": "审定合并利润表归母净利润 210,084,260.07 元，折算 21,008.43 万元",
  "evidence_ids": ["EVD-0001", "EVD-0002"],
  "counter_arguments": [
    "检查是否为母公司口径",
    "检查是否为扣非口径",
    "检查元/万元折算和四舍五入"
  ],
  "root_cause": "加期更新不同步",
  "recommendation": "请核对审定数后统一为 21,008.43 万元，并同步其他文件",
  "related_locations": ["对照文件/问题六/表 8"],
  "coverage_status": "COMPLETE",
  "review_status": "OPEN",
  "review_note": ""
}
```

`impact` 只使用 A/B/C。`evidence_status` 只使用五档状态。`review_status` 在续核任务中使用：

- `OPEN`：尚未处理；
- `FIXED`：已修复；
- `PARTIAL`：部分修复；
- `NOT_FIXED`：未修复；
- `NOT_APPLICABLE`：确认不适用；
- `REGRESSION`：修订引入新问题。

## 六、候选与确认

只有满足以下条件，finding 才能从 `CANDIDATE` 升级为 `CONFIRMED`：

- 已回到原始段落、表格、单元格、公式或原始来源；
- 主体、期间、口径、单位、币种一致；
- 差异不属于四舍五入、合并单元格、分类小计、两层合计或加减结构误报；
- 权威来源明确，或来源冲突已经由项目组/专业人士决定；
- A 级问题至少完成三项反证尝试。

以下情况不得升级为 `CONFIRMED`：

- OCR、模型、模糊匹配或语义相似度命中；
- 来源只存在于搜索摘要、转载页或无法确认主体的网页；
- 同一事实的权威来源互相矛盾；
- 需要猜测缺失数字、期间、币种或单位；
- 只能通过润色、改写或改变风格解决。

## 七、覆盖状态

对每个表格、关键 claim、章节和外部来源记录：

- `COMPLETE`：按范围完成；
- `PARTIAL`：部分完成，列出已完成和未完成；
- `NOT_RUN`：未执行，说明原因；
- `UNVERIFIABLE`：证据不足，无法形成结论；
- `NOT_IN_SCOPE`：用户明确排除或经确认不适用。

覆盖状态不得以"没有报错"代替。未覆盖项必须在 Excel 总览页、`manifest.json` 和交付说明中同步出现。

## 八、校验

使用 `scripts/validate_review_artifacts.py` 检查：

- ID 唯一；
- claim/source/evidence/finding 引用存在；
- CONFIRMED finding 必须有证据；
- A 级 CONFIRMED 至少有 3 条反证记录；
- UNVERIFIABLE 必须有原因；
- finding 的文件角色和定位存在；
- coverage 状态合法；
- manifest、ledger、findings 的时间顺序合理。
