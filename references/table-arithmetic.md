# 表格算术验算 + 误报识别

> 批量验算"合计=分项和"是复核的第一步，但误报率很高。本文件给验算代码 + 误报过滤规则。文中项目名称均为历史项目实测示例，仅说明方法，不得当作当前任务事实。

## 1. 批量验算含"合计/小计/总计"行的表格

```python
import docx
from docx import Document

def num(s):
    s = str(s).replace(",", "").replace("，", "").replace(" ", "").replace("%", "")
    try: return float(s)
    except: return None

doc = Document(path)
issues = []
for ti in range(len(doc.tables)):
    t = doc.tables[ti]
    if len(t.rows) < 3:
        continue
    for ri in range(len(t.rows)):
        if t.rows[ri].cells[0].text.strip() in ("合计", "小计", "总计") and ri > 0:
            ncols = len(t.rows[ri].cells)
            for ci in range(1, min(ncols, 8)):
                tv = num(t.rows[ri].cells[ci].text) if ci < len(t.rows[ri].cells) else None
                if tv is None: continue
                s = 0; cnt = 0
                for rj in range(ri):   # 上方所有行该列数值之和（简单累加，会误报）
                    if ci < len(t.rows[rj].cells):
                        v = num(t.rows[rj].cells[ci].text)
                        if v is not None:
                            s += v; cnt += 1
                # 粗筛阈值 = 定级上限 0.05（见第 8 节）；粗筛只能多报不能漏报，命中只产 CANDIDATE
                if cnt >= 2 and abs(s - tv) > 0.05:
                    issues.append((ti, ri, ci, s, tv, cnt))
            break
```

## 2. 误报过滤（批量脚本命中后，先过这五道关卡再定性）

| 关卡 | 判断 | 处理 |
| --- | --- | --- |
| ① 合并单元格假错位 | 合计行前几列是合并单元格（`['合计','合计',...]`），或 gridSpan>1 / vMerge | 用 `build_logical_grid` 展开为逻辑列网格后重算，多为误报 |
| ② 分类小计 | 表内有"一、XX""二、XX"分组行，各自有小计，合计=小计之和而非全部明细之和 | 改验"小计之和=合计"，或"各组明细和=小计" |
| ③ 两层合计 | 存在中间合计行（如"主营业务成本=直接材料+直接人工+制造费用"，"合计=主营业务成本+其他业务成本"） | 按层级分层验算，不要跨层累加 |
| ④ 加减结构 | 合计 = A + B − C + D（如"财务费用=利息费用−利息收入+手续费"） | 识别正负号/减项后再验算 |
| ⑤ 合计行与明细行列结构不一致 | 合计行"合计"跨"序号+名称"两列后只剩 3 个数值列，按明细行列号取合计行会错位 | 用"合计行数值按顺序对齐明细列"（见第 2.1 节） |

### 2.1 表格结构诊断函数（方案 4：批量验算前的强制前置步骤）

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

def build_logical_grid(table):
    """gridSpan 展开为占位列，返回逻辑列网格"""
    grid = []
    for row in table.rows:
        logical_row = []
        for text, span, _ in iter_row_cells_raw(row):
            logical_row.append(text)
            for _ in range(span - 1):
                logical_row.append(None)
        grid.append(logical_row)
    return grid

def diagnose_table(table, table_idx):
    """批量验算前打印表格真实结构（含 gridSpan/vMerge 标记），确认不是合并单元格导致的假象"""
    print("=== 表%d 结构诊断 ===" % table_idx)
    for ri, row in enumerate(table.rows):
        cells_info = []
        for text, span, vm in iter_row_cells_raw(row):
            mark = ""
            if span > 1: mark += "[G%d]" % span
            if vm: mark += "[V]"
            cells_info.append("%s%s" % (mark, text[:20]))
        print("R%d: %s" % (ri, " | ".join(cells_info)))
    # 示例输出：R5: [G2]合计 | | 518,132.37 | 712,028.63 | 750,640.00
    # 一眼看出"合计"跨 2 列、后续 3 个数值列——不会再误判为"合计行右移一列"
```

### 2.2 合计行与明细行分开处理（方案 3：合计行列结构不一致时的对齐）

合计行的列结构往往与明细行不同（"合计"跨列）。**不要用明细行的列号取合计行**，而是按"数值出现顺序"与明细列对齐：

```python
def get_sum_row_values(table, sum_row_idx, detail_col_map):
    """合计行按'数值出现顺序'与明细列对齐"""
    grid = build_logical_grid(table)
    sum_row = grid[sum_row_idx]
    # 合计行的非空值（跳过"合计"文本和 None 占位）
    sum_vals = [v for v in sum_row[1:] if v]  # 跳过第一列"合计"
    detail_cols = [h for h in detail_col_map if h]
    if len(sum_vals) != len(detail_cols):
        # 列数不匹配：合计行可能跨列，按顺序对齐
        return dict(zip(detail_cols, sum_vals))
    return dict(zip(detail_col_map, sum_vals))

# 用法：合计行 ['合计', '518,132.37', '712,028.63', '750,640.00']（3 个值）
# 与明细列 ['2023年', '2024年', '2025年'] 按顺序对齐，不会错位
```

**铁律**：批量验算"合计=分项和"或"列错位"前，**必须先运行 `diagnose_table` 打印真实结构**，确认不是合并单元格导致的假象（gridSpan/vMerge/合计行跨列），再定性。禁止直接采信 `row.cells` 的友好视图。

## 3. 验算范例（命中后如何精确核查）

```python
# 发现"表N R行 列C 差异X"，先打印原始单元格（不去重）确认结构：
t = doc.tables[ti]
for ri, row in enumerate(t.rows):
    print(f"R{ri}: {[c.text.strip() for c in row.cells]}")
# 再人工判断属于 ①~④ 哪一类，或确为真实算术差异
```

## 4. 真实算术差异的判定标准

只有同时满足以下条件，才判定为真实算术差异（B 级）：
- 该表无合并单元格、无分类小计、无中间合计、无加减结构；
- 分项之和对齐后与合计行确有偏差，且偏差超出四舍五入范围（>0.05）；
- 用未舍入数据复算仍不吻合。

例（本次实测真实问题）：前八大客户应收账款表，应收账款合计与 8 客户之和一致，但**坏账准备合计 3,631.38 ≠ 8 客户之和 3,623.15（差 8.23 万元）**，且 8 客户各自的坏账准备与"应收账款×计提比例"均自洽 → 合计行抄录/取数错误。

## 5. 率×基数=金额（借自 prospectus-review gotcha #3）

```python
# 占比×总额应≈披露的分项金额；毛利率×收入应≈毛利额
# 只核"跨表一致"会漏掉这类错
calc_amount = rate / 100 * base
# 容差按舍入误差推导：披露率按 0.01% 舍入 → 金额误差 ≤ base×0.00005；分项金额自身舍入 ≤0.005 万
tol = abs(base) * 0.00005 + 0.05
flag = "✓" if abs(calc_amount - disclosed_amount) < tol else f"✗ 复算{calc_amount:.2f} vs 披露{disclosed_amount}"
```

## 6. 完成率 / 增长率 / 占比 复算

```python
# 完成率 = 实现数 / 预测数；增长率 = 本期/基期 - 1；占比 = 分项/合计
# 表内披露值用未舍入数据复算，尾差 ≤0.01 个百分点判"通过"（与第 8 节一致），否则列问题
calc = impl / pred * 100
disp = float(rate.replace('%',''))
flag = "✓" if abs(calc - disp) < 0.01 else f"✗ 复算{calc:.2f}% vs 表列{disp}%"
```

## 7. 平均值无法复算的口径问题

表末"平均值"若无法用简单算术平均、也无法用已知权重（如收入）加权复算，属**口径待确认**（B 级）：疑似按未披露的权重（如辆份价值×销量）加权，需评估师/项目组确认口径，不要直接判"计算错误"。

## 8. 统一容差与证据状态

- 直接对碰的两个显示值：默认容差 `0.011` 万元；
- 多项已舍入分项相加：可解释尾差上限默认 `0.05` 万元，超过后必须用未舍入数据复算；
- 百分比：默认可解释尾差上限 `0.01` 个百分点，且必须确认分母相同；
- 项目另有指定容差时，写入 `manifest.json` 并全流程统一。

**两段式阈值纪律**：批量脚本的命中阈值（粗筛线）一律不得宽于本节定级上限——粗筛只能多报、不能漏报；命中只产生 `CANDIDATE`，必须用未舍入数据复算并排除误报后，才能按本节阈值定级为 `CONFIRMED`。

批量脚本命中只产生 `CANDIDATE`。只有回原始单元格、确认表格结构、复算未舍入数据并排除误报后，才能升级为 `CONFIRMED`。每个确认问题写入 `finding.schema.json`，并在 `counter_arguments` 中记录反证尝试。
