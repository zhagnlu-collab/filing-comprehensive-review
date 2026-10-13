# 加期漏更新检测（报告书/回复加期后）

> 加期（如报告期从"2024、2025"扩为"2024、2025、2026年1-6月"）后，检查"应更新到最新报告期却未更新"的地方。本文件给判定口径 + 检测代码。文中期间与项目名称均为历史项目示例；脚本期间必须从 `manifest.json` 读取，禁止写死。

## 1. 判定口径（先与用户确认）

| 类别 | 是否加期 | 说明 |
| --- | --- | --- |
| 标的公司及重要子公司自身财务数据 | **应加期** | 从两期扩为三期；资产负债表为三时点 |
| 备考报表（利润表收入/利润、资产负债表资产/负债） | **应加期** | 更新到最新一期 |
| 商誉金额 | 视情况 | 若因加期变化，重组报告书+问询回复同步更新；否则不更新 |
| 管理层讨论与分析（收入/成本/费用/利润/资产负债/现金流量/偿债/营运） | **应加期** | 均覆盖最新一期 |
| 风险因素章节财务数据引用 | **应加期** | 上期"2024、2025"两期 → 本期改"2024、2025、2026年1-6月"三期 |
| 期间/时点表述（报告期各期、最近两年、截至2025年末） | **应更新** | 反映新报告期 |
| 财务资料有效期 | **须重算** | 最近一期经审计财务资料有效期 6 个月（符合条件可申请延长，延长上限以现行 26 号准则及交易所审核规则为准）；加期后按新申报时点重算，超期须补充最近一期财务报告和审计/审阅（26 号准则第六十九条） |
| 股东大会决议及授权有效期 | **须核验** | 加期常伴随决议/授权过期；过期须重新履行程序后再申报 |
| 评估备案/批文有效期 | **须核验** | 国资评估备案、发改/行业批文等须在有效期内方可沿用；过期须重新办理 |
| 引用第三方数据（行业、可比公司） | **应更新** | 更新至最近一期年报/半年报口径，并标注来源与时点 |
| 交易对方财务数据 | **不加期** | 交易对方自身报表数据 |
| 评估口径（评估值/基准日/折现率/溢余资产/投资性房地产） | **不更新** | 评估基准日未变 |
| 历史事实（沿革/前次评估/改制/行政处罚"最近三年"） | **不更新** | 法规固定表述或历史事实 |

## 2. 接受修订后正文提取（关键，先做对）

加期版文件常有大量修订痕迹（w:ins/w:del）。python-docx 的 `p.text`/`p.runs` 会漏掉 w:ins 里的插入文本，导致提取残缺（如"2026年8月31日"被读成"月31日"）。正确做法：

```python
def para_text(p):
    # 含 w:ins 里的 w:t，排除 w:del 下的删除文本
    return "".join(t.text for t in p._element.xpath('.//w:t[not(ancestor::w:del)]') if t.text)

def cell_text(c):
    return "".join(t.text for t in c._tc.xpath('.//w:t[not(ancestor::w:del)]') if t.text).strip()
```

## 3. 期数列检测（找"仍两期、缺最新期"的表）

```python
import json, re
from docx import Document

# 期间一律从 manifest.json 读取，禁止写死（历史项目写死年份导致换项目即失效）
with open("manifest.json", encoding="utf-8") as f:
    scope = json.load(f)["scope"]
periods = scope["report_periods"]            # 如 ["2024", "2025", "2026H1"]
latest = scope["latest_period"]              # 如 "2026H1"
prev_years = sorted({re.match(r"(\d{4})", p).group(1) for p in periods if p != latest})
latest_year = re.match(r"(\d{4})", latest).group(1)

doc = Document(path)

def cell_text(c):
    return "".join(t.text for t in c._tc.xpath('.//w:t[not(ancestor::w:del)]') if t.text).strip()

results = []
for ti in range(len(doc.tables)):
    t = doc.tables[ti]
    header_cells = set()
    for ri in range(min(3, len(t.rows))):
        for c in t.rows[ri].cells:
            txt = cell_text(c)
            if txt:
                header_cells.add(txt)
    header_text = " ".join(header_cells)
    is_fin_table = any(re.search(y + r"\s*年|" + y + r"年度", header_text) for y in prev_years)
    has_latest = latest_year in header_text
    if is_fin_table and not has_latest:
        results.append((ti, header_text[:150]))
```

## 4. 判断章节归属（决定是否应更新）

批量检测命中"两期表"后，**必须回查该表前面的章节标题**，判断它属于评估章节还是审计/经营章节：

```python
# 构建 body 顺序的段落+表格序列，找目标表前面最近的标题段落
body = doc.element.body
items = []
pi = 0; ti = 0
for child in body.iterchildren():
    tn = child.tag.split('}')[-1]
    if tn == 'p':
        items.append(('p', pi, para_text(doc.paragraphs[pi])))
        pi += 1
    elif tn == 'tbl':
        items.append(('tbl', ti, ''))
        ti += 1

def find_heading_before(tbl_idx):
    pos = next(i for i,(t,i2,tx) in enumerate(items) if t=='tbl' and i2==tbl_idx)
    headings = []
    for j in range(pos-1, max(pos-30, -1), -1):
        t, idx, txt = items[j]
        if t=='p' and txt and len(txt)<60 and (txt[0] in '一二三四五六七八九十（(' or txt[0].isdigit()):
            headings.append(txt[:60])
            if len(headings)>=3: break
    return headings
```

**判定**：表在"评估"章节（如"（三）未来净现金流的预测 / 营业收入的预测 / 历史年度营业收入"）→ 评估口径，不要求加期；表在"管理层讨论与分析""关联交易""风险因素""财务会计信息"等审计/经营章节 → 应加期，两期=漏更新。

## 5. 期间/时点表述扫描

```bash
# 期间表述
grep -nE "报告期|最近两年|最近一年|最近一期|近两年|近三年" 文件.txt
# 时点表述（需区分评估基准日 vs 报告期期末）；年份按 report_periods 替换，禁止写死
grep -nE "截至2025年12月31日|截至2025年末|2025年12月31日" 文件.txt
```

命中后逐个判断：
- "截至上一完整年度末"出现在评估语境（评估基准日、P/E 估值）→ 合理保留；
- 出现在财务数据时点（如"最近一期简要财务报表""报告期各期末"）→ 应更新到最新一期期末。

## 6. 上期 diff（找"应扩三期却仍两期"）

提取上期、本期全文后，对比同章节的财务数据表述：上期"2024年、2025年"两期并列，本期仍"2024年、2025年"两期（未加最新一期）= 漏更新。

## 7. 典型漏更新形态（实测）

- 财务数据表仍两期（缺最新一期列）；
- "最近一期简要资产负债表/利润表"时点仍停在旧报告期末（应更新到最新一期）；
- 风险因素章节财务引用仍停留旧两期；
- 关联交易章节的"报告期各期"数据（如关联方资金拆借）仍两期；
- 备考报表未更新到最新一期。
