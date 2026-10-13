# 底稿穿透与 PDF 解析

> SKILL.md 阶段 C 第 3 项"底稿穿透"的执行方法。目标：把 Word 引用值逐层追到"Excel 汇总 → 公式链 → TB/审计报告签署版"源头凭证，每层留 `EVD-` 证据。文中示例来自历史项目，仅说明方法。

## 1. 穿透链条

`Word 引用值 → Excel 汇总单元格 → 公式链上溯 → TB/明细表 → 审计报告签署版（或评估说明、法律意见书）`

任一层断链（找不到来源、公式无缓存值、TB 缺失），该 claim 标记 `UNVERIFIABLE` 并写明断点层，不得写成一致。

## 2. Word 引用值 → 底稿定位（数值索引反查）

```python
# 对全部底稿 Excel 建立 值 → (工作簿, 工作表, 单元格) 索引，用 Word 值反查底稿位置
import openpyxl
from collections import defaultdict

def build_value_index(xlsx_paths):
    idx = defaultdict(list)
    for path in xlsx_paths:
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for cell in row:
                    v = cell.value
                    if isinstance(v, (int, float)) and v != 0:
                        idx[round(float(v), 2)].append((path, ws.title, cell.coordinate))
    return idx

# 注意元/万元折算：Word 值 ×10000 和 ÷10000 两种口径都要查
```

## 3. Excel 公式链上溯

```python
wb_f = openpyxl.load_workbook(path, data_only=False)  # 读公式
wb_v = openpyxl.load_workbook(path, data_only=True)   # 读缓存值
```

1. 从汇总单元格读公式，正则提取引用：`(?:'([^']+)'|([\w一-鿿]+))!(\$?[A-Z]+\$?\d+(?::\$?[A-Z]+\$?\d+)?)`；
2. 逐层上溯至无公式引用的输入层（TB 层/手工录入层）；
3. **缓存值陷阱**：Excel 保存时未重算，`data_only=True` 读到的是过期缓存。汇总单元格有公式但缓存值 ≠ 按引用单元格重算的值时，说明底稿未重算，其缓存值不得直接作权威值，须重算或回源头；
4. 跨工作簿外部链接公式（`[1]Sheet!A1` 形式）须找到被链接工作簿，找不到记 `UNVERIFIABLE`。

## 4. 审定 Excel ≠ 签署版审计报告（高频坑）

- 项目组流转的"审定报表.xlsx"可能不是最终签署版；**权威值以签署版审计报告（PDF/纸质扫描件）为准**；
- 逐科目对碰：审定 Excel 关键科目（至少：资产总计、负债合计、归母权益、营业收入、净利润、归母净利润、经营活动现金流量净额）与签署版审计报告正文数字核对；不一致时以签署版为准并记 finding；
- 审计报告附注与主表矛盾、附注与 TB 矛盾，同法处理。

## 5. PDF 解析路径

```python
import pdfplumber  # 或 fitz（PyMuPDF）
with pdfplumber.open(path) as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        tables = page.extract_tables()
```

- 有文本层：直接提取，定位用"报告名 + 第 N 页"；
- 扫描件（无文本层）：OCR 结果**只产生 `CANDIDATE`**，必须回原件人工确认后才能升级；在 coverage 中记录"扫描件 OCR 覆盖"及低置信度页码；
- 表格提取优先 `extract_tables()`；跨页拼接表、无线表必须人工复核；
- 大面积图片、盖章遮挡区域标记 `NOT_IN_SCOPE` 或 `UNVERIFIABLE`。

## 6. 证据落账

- 每个穿透层级的来源都登记为 `SRC-`（工作簿定位到单元格、报告定位到页码）；
- 比对结果登记 `EVD-`（relation=support/refute），缓存值过期、外部链接断链等记入 `note`；
- 断链、缺层、版本存疑的 claim 一律 `UNVERIFIABLE`，不得写成一致。
