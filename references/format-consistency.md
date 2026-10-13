# 格式与表述一致性检查

> 借自另一 AI 质检报告的轻量级检查项：格式一致性（全角/半角、单位、日期格式）与主体名称一致性。这些不属于数据勾稽，但影响披露专业度与可读性，属 C 级问题。

## 1. 全角/半角字符

| 检查项 | 规则 | 检查方法 |
|--------|------|---------|
| 千分位逗号 | 数字千分位应统一用半角 `,`（如 `1,501.7`），不得混入全角 `，`（如 `1，501.7`） | 正则 `\d+，\d{3}` 扫描全角逗号数字 |
| 半角逗号/句号 | 中文句子里出现 `,` `.` 而非 `，` `。`（数字千分位、小数点、英文缩写、网址、代码除外） | 中文上下文中的 `[a-zA-Z0-9],[一-鿿]` 模式 |
| 乘号 | 应为 `×`，不得用半角 `*`（如"4.50 元/股 \*（1+变动比例）"） | 扫描 `\*` 在数学表达式中的使用 |

## 2. 单位一致性

| 检查项 | 规则 | 检查方法 |
|--------|------|---------|
| 面积单位 | 同一文件中"平方米"与"㎡"统一 | 全文扫描两种写法的出现位置 |
| 金额单位 | 同一表述句中"万元"与"亿元"混用（如前半句"958.58 万元"后半句"1.39 亿元"） | 同句内万元/亿元并存检测 |
| 表格单位标注 | 表格上方"单位：股"但表内为"元/股"与"%" | 表头单位声明 vs 表内实际单位比对 |

## 3. 日期格式一致性

同一文件中日期格式应统一，常见三种：
- `YYYY年MM月DD日`（如 2024年6月26日）
- `YYYY-MM-DD`（如 2019-09-18）
- `YYYY.MM.DD`（如 2024.01.01）

**检查方法**：统计三种格式出现次数，若同一文件混用三种且分布散乱（非章节级统一），提示统一。报告期/期间表述（如"2025年度/2025.12.31"）也建议统一为中文年月日格式。

## 4. 主体名称一致性

同一主体的全称/简称在全文中应统一：
- 例：表 3 用"新疆大道专用装备有限公司"，表 4 用"新疆大道专用设备公司"——"装备"误作"设备"，名称对不上会直接影响核查对应关系；
- 例：表内用"东实非金属（武汉）有限公司广州分公司"，正文用"武汉非金属广州分公司"——省去"东实"且语序倒置，易误为独立主体。

**检查方法**：
1. 提取全部企业全称（含"有限公司/股份/集团"后缀）；
2. 对每个全称，扫描其**子串变体**（去"有限/股份"后缀、语序变化、单字增删）；
3. 同一主体的不同写法并列，提示统一为工商登记全称（表内口径），并在首次出现处定义简称。

## 5. "无交易"表述一致性

同一主体同一期间的"无交易"表述应统一：
- 例：表 6 填"0.00"，表 4/表 5 同期填"-"——同一主体同一期间"0.00"与"-"并存。

**检查方法**：同一主体同一期间，扫描"0.00""-""—""/"的混用。

## 6. 格式复核（重组报告书和问询回复必做）

### 6.1 高亮字体检测

**规则**：正式申报文件不得含高亮字体（`w:highlight` val≠"none"）。

**检查方法**：
```python
from lxml import etree
import zipfile, re

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

def check_highlight(path):
    z = zipfile.ZipFile(path)
    root = etree.fromstring(z.read("word/document.xml"))
    highlights = []
    for r in root.iter("{%s}r" % NS["w"]):
        rpr = r.find("w:rPr", NS)
        if rpr is not None:
            hl = rpr.find("w:highlight", NS)
            if hl is not None:
                val = hl.get("{%s}val" % NS["w"])
                if val and val != "none":
                    text = "".join(t.text or "" for t in r.iter("{%s}t" % NS["w"]))
                    highlights.append({"text": text[:50], "color": val})
    return highlights
```

### 6.2 非黑色字体检测

**规则**：正式申报文件应为黑色字体（`w:color` val="000000"/"auto"/空）。深灰色（如 1C1F23/333333）属排版样式，可标注为提示级；彩色（如 FF0000/0000FF）属格式问题。

**检查方法**：
```python
def check_non_black(path):
    z = zipfile.ZipFile(path)
    root = etree.fromstring(z.read("word/document.xml"))
    non_black = []
    for r in root.iter("{%s}r" % NS["w"]):
        rpr = r.find("w:rPr", NS)
        if rpr is not None:
            color = rpr.find("w:color", NS)
            if color is not None:
                val = color.get("{%s}val" % NS["w"])
                if val and val.lower() not in ("000000", "auto", ""):
                    text = "".join(t.text or "" for t in r.iter("{%s}t" % NS["w"]))
                    non_black.append({"text": text[:50], "color": val})
    return non_black
```

### 6.3 修订痕迹检测（A 级问题）

**规则**：正式申报前**必须接受全部修订**（`w:ins`=0/`w:del`=0）。存在未接受修订即记为 A 级问题。

**检查方法**：
```python
def check_track_changes(path):
    z = zipfile.ZipFile(path)
    xml = z.read("word/document.xml").decode("utf-8", "ignore")
    ins_count = len(re.findall(r"<w:ins\b", xml))
    del_count = len(re.findall(r"<w:del\b", xml))
    return {"ins": ins_count, "del": del_count}
```

**判定标准**：
- ins=0 且 del=0 → 通过（已接受全部修订）；
- ins>0 或 del>0 → A 级问题（存在未接受修订，正式申报前必须接受全部修订）。

## 7. 尾差说明

合计数与分项之和存在四舍五入尾差（≤0.05 万元或 0.01 个百分点）时，建议在表下加注"合计数与分项之和的差异系四舍五入所致"，或在正文统一取数口径。

## 8. 判定优先级

| 级别 | 问题类型 |
|------|---------|
| C 级（提示） | 全角/半角、单位、日期格式、尾差说明 |
| B 级（口径待确认） | 主体名称不一致（影响核查对应关系）、"无交易"表述不统一 |
