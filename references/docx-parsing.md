# DOCX 精确解析（python-docx）

> 本次复核使用的核心解析代码模板。依赖 python-docx（1.2.0+），建议用托管 venv 解释器。文中"本项目"均指历史实测项目，仅作示例。

## 1. 全文提取（段落 + 表格，按文档顺序）

```python
import docx
from docx import Document

doc = Document(path)
lines = []
body = doc.element.body
pi = 0; ti = 0
for child in body.iterchildren():
    tag = child.tag.split('}')[-1]
    if tag == 'p':
        txt = "".join(r.text for r in child.xpath('.//w:t') if r.text).strip()
        if txt:
            lines.append(f"P{pi}: {txt}")   # 段落：P+序号（序号在文件内稳定，但跨文件会漂移）
        pi += 1
    elif tag == 'tbl':
        tbl = doc.tables[ti]
        lines.append(f"\n[表{ti}]")
        for row in tbl.rows:
            cells = []
            for c in row.cells:
                x = c.text.strip().replace("\n", " ")
                if x and x not in cells:      # 去重合并单元格的重复值（会丢失合并信息，仅用于速览）
                    cells.append(x)
            lines.append(" | ".join(cells))
        lines.append(f"[/表{ti}]\n")
        ti += 1
full = "\n".join(lines)
```

> 注意：上面的"去重"版本适合快速浏览；**精确定位/验算时必须用原始单元格**（见第 4 节），否则合并单元格会被误判为错位。

## 2. 楷体加粗识别（直接格式 + 样式继承）

```python
NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def run_is_kai(r):
    """判断 run 是否楷体（含样式继承）；加粗同理，把字体判断换成 <w:b> 即可"""
    east = None; fname = None
    if r._element.rPr is not None and r._element.rPr.rFonts is not None:
        east = r._element.rPr.rFonts.get(NS+'eastAsia')
        fname = r._element.rPr.rFonts.get(NS+'ascii')
    kai = False
    if east and '楷' in str(east): kai = True
    if fname and '楷' in str(fname): kai = True
    # 样式继承：段落样式 / 字符样式的楷体（需另读 styles.xml，按 styleId 查字体）
    return kai
```

样式继承的加粗/字体判断，需解压 `word/styles.xml`，按 styleId 正则匹配对应 `<w:style>` 段内是否含 `<w:b/>` 或 "楷体"。

## 3. 修订痕迹精确统计（避开 w:insideH 陷阱）

```python
import zipfile, re
z = zipfile.ZipFile(path)
xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
# 错误：xml.count("<w:ins")  会误匹配 <w:insideH>（表格内边框）
# 正确：用 \b 匹配标签边界
ins = len(re.findall(r'<w:ins\b', xml))
dels = len(re.findall(r'<w:del\b', xml))
```

## 4. 合并单元格精确解析（治本：原始单元格 + gridSpan/vMerge 展开为逻辑列）

> **这是解决 Word 表格合并单元格串行/假错位的治本方案。** python-docx 的 `row.cells` 是"友好视图"（对横向合并 gridSpan 返回重复值、对纵向合并 vMerge 返回空值/延续值），按固定列号取数必然串行。**必须遍历原始 `w:tc`，读取每个单元格的 `gridSpan` 和 `vMerge`，展开为逻辑列网格。**

### 4.1 合并单元格串行的四种根因

1. **横向合并（gridSpan）返回重复值**：`['合计', '合计', '518,132.37', ...]`——前两个'合计'是同一合并单元格，按位置取 `cells[2]` 会串行；
2. **纵向合并（vMerge）返回空值/延续值**：第二行 `cell[0]` 返回空或延续上一行，按"每行第一列是行名"假设取值会错位；
3. **横向+纵向混合合并（多级表头）**：表头两行，第一行横向合并，第二行各占一列，cells 长度和值因合并方式不同而变化；
4. **合计行与明细行列结构不一致**：合计行"合计"跨"序号+名称"两列后只剩 3 个数值列，按明细行列号取合计行会错位（本项目表 36/37 的真实错位案例）。

### 4.2 原始单元格遍历（返回 text + gridSpan + vMerge_continue）

```python
from docx.oxml.ns import qn

def iter_row_cells_raw(row):
    """按真实结构遍历行单元格，返回 (text, gridSpan, vMerge_continue)"""
    for tc in row._tr.tc_lst:
        tcPr = tc.find(qn('w:tcPr'))
        grid_span = 1
        vmerge_continue = False
        if tcPr is not None:
            gs = tcPr.find(qn('w:gridSpan'))
            if gs is not None:
                grid_span = int(gs.get(qn('w:val'), '1'))
            vm = tcPr.find(qn('w:vMerge'))
            if vm is not None:
                val = vm.get(qn('w:val'))
                vmerge_continue = (val == 'continue') or (val is None and vm.text is None)
        text = "".join(t.text or "" for t in tc.iter(qn('w:t')))
        yield (text.strip(), grid_span, vmerge_continue)
```

### 4.3 构建逻辑列网格（gridSpan 展开为占位列）

```python
def build_logical_grid(table):
    """把 gridSpan 展开为占位列，返回逻辑列网格（与表头列号完全对齐）"""
    grid = []
    for row in table.rows:
        logical_row = []
        for text, span, _ in iter_row_cells_raw(row):
            logical_row.append(text)
            for _ in range(span - 1):
                logical_row.append(None)  # 合并占位
        grid.append(logical_row)
    return grid

# 效果：合计行 ['合计', None, '518,132.37', '712,028.63', '750,640.00']，列号与表头完全对齐
```

### 4.4 表头锚点列定位（方案 2：多级表头按含义取列）

```python
def parse_header_columns(table, header_rows=2):
    """解析多级表头，返回 {逻辑列号: '期间+指标'}"""
    grid = build_logical_grid(table)
    headers = []
    for ci in range(len(grid[0])):
        parts = []
        for ri in range(header_rows):
            if ri < len(grid) and grid[ri][ci]:
                parts.append(grid[ri][ci])
        headers.append(" ".join(parts))
    return headers  # ['项目', '2026年1-6月 实现数', '2026年1-6月 预测数', ...]

def find_col(headers, keyword):
    """按含义找列号"""
    for ci, h in enumerate(headers):
        if keyword in h:
            return ci
    return -1

# 用法：即使表格有合并单元格，只要表头能解析，就能按"2026年1-6月 实现数"准确定位列
```

**铁律**：批量验算发现"合计≠分项和"或"列错位"时，先用 `build_logical_grid` 展开为逻辑列网格，确认真实列结构后再定性，禁止直接采信 `row.cells` 的友好视图。

## 5. 图片与图形载体的提取与定位（必做，不得跳过）

> 结构图、关系图、流程图承载的往往是关键比例与主体数据。**只统计图片数量而不提取内容，等于该载体零覆盖。** 解析阶段必须产出 `kind='image'` 的块，把图当作与段落、表格并列的第三类载体。

```python
import os, zipfile
import xml.etree.ElementTree as ET

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
V = 'urn:schemas-microsoft-com:vml'

def imgs_of(p_el):
    """段落内嵌图片的 rId（DrawingML 与 VML 两种写法都要覆盖）"""
    rids = []
    for blip in p_el.iter('{%s}blip' % A):
        rid = blip.get('{%s}embed' % R)
        if rid:
            rids.append(rid)
    for im in p_el.iter('{%s}imagedata' % V):
        rid = im.get('{%s}id' % R)
        if rid:
            rids.append(rid)
    return rids

def walk_with_images(path, outdir):
    """按文档顺序遍历 body，返回 [(kind, text, [media...])]，并把图片导出到 outdir"""
    z = zipfile.ZipFile(path)
    z.extractall(outdir)
    doc = ET.parse(os.path.join(outdir, 'word', 'document.xml'))
    rels = ET.parse(os.path.join(outdir, 'word', '_rels', 'document.xml.rels'))
    rmap = {r.get('Id'): r.get('Target') for r in rels.getroot()}
    body = doc.getroot().find('{%s}body' % W)

    seq = []
    last_text = ''                      # 用于给图片打"上文标签"
    for child in body:
        tag = child.tag
        if tag == '{%s}p' % W:
            txt = ''.join(t.text or '' for t in child.iter('{%s}t' % W)).strip()
            media = [os.path.basename(rmap.get(r, r)) for r in imgs_of(child)]
            if media:
                seq.append(('image', last_text, media))   # 图：附带前一段文本
            if txt:
                seq.append(('p', txt, []))
                last_text = txt
        elif tag == '{%s}tbl' % W:
            seq.append(('table', '', []))
    return seq

# 用法：遍历 seq，对 kind=='image' 且上文命中
# 结构图|关系图|示意图|流程图|股权结构|产权控制关系|组织架构
# 的条目，必须逐张放大识读并纳入比对。
```

### 5.1 逐张识读（放大裁切）

```python
from PIL import Image
im = Image.open('figs/xxx.png')
w, h = im.size
# 长图分段放大，避免缩放后文字不可辨
top = im.crop((0, 0, w, int(h*0.6)))
top = top.resize((top.width*2, top.height*2), Image.LANCZOS)
top.save('figs/xxx-top.png')        # 再逐张读取识认
```

**数字区域必须单独再放大一次（4–6 倍）逐字符复核**：

```python
# 只截比例数字所在的小区域，放大到能逐字符辨认为止
box = (620, 110, 1000, 220)          # 先粗定位，再按需收窄
c = im.crop(box); c = c.resize((c.width*5, c.height*5), Image.LANCZOS)
c.save('figs/xxx-zoom.png')          # 逐字符读，确认每一位数字
```

**为什么必须做**：图像识读本身是误判来源。实测中把结构图的 `69.99%` 目视读成 `69.00%`，据此判定"文件笔误、该层合计仅 99.01%"，实为识读误差。**凡拟据图内数字出 finding，必先放大逐字符复核；图内数字与工商登记"接近但不相等"时，先怀疑自己的眼睛。** 复核结论与原读不一致时，以复核结论为准，并把放大件归档为证据、在交付物中注明更正。

### 5.2 逐层比例核对（**提示工具，不是判据**）

识读时逐层把各主体比例相加。**但合计不足 100% 本身不构成错误**——它只说明"该层还有主体未列示"，属于**提示**：

1. 先回源披露判据（见 `cross-carrier-consistency.md` 步骤 0）。以产权及控制关系结构图为例，准则只要求披露"与控股股东、实际控制人之间的产权及控制关系"，**不要求把该层股东名册列全**；
2. 再用工商登记一层股东/合伙人名单反查未列示的是谁；
3. 只有未列示者属于**控股股东、实际控制人及其控制链上的主体**时，才构成问题；未列示者是非控股股东（无论 0.59% 还是 17.54%）、或是不执行合伙事务的有限合伙人，**均不构成问题**。

> 实测教训：曾按"合计须为 100%"把 3 条"遗漏非控股股东"报成 A 级问题，全部为误报。**标准错了比执行不到位更伤交付信任。**

## 6. Excel 底稿读取（openpyxl，托管 python）

```python
import openpyxl
wb = openpyxl.load_workbook(path, data_only=True)   # data_only=True 读缓存值
# 读公式（非缓存值）用 data_only=False
wb2 = openpyxl.load_workbook(path, data_only=False)
# 大表用 read_only=True 流式读取
wb3 = openpyxl.load_workbook(path, data_only=True, read_only=True)
```
