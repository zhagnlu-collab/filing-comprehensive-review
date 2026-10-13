# CHANGELOG

## 3.3.0（2026-10-13）

- 新增 `references/transaction-substance-review.md`：经用户确认的 12 类交易实质与披露支撑方法，涵盖主体关系、历史沿革、实施程序、合同条件、权属瑕疵、资金往来、财务因果、估值与预测、募集资金、外部比较及风险承诺。
- 主文件及披露复核细则补充按需读取入口，与现有数据勾稽、底稿追溯和续核方法衔接；不纳入学习资料的项目名称、数字或批注原文。


## 3.2.0（2026-09-26）

北交所规则体系落地 + 26 号准则条款映射逐条校准 + 旧格式兼容迁移。

**新增**
- `references/rule56-bse-checklist.md`：北交所 56 号准则（证监会公告〔2023〕23 号）逐条检查清单，按准则重新公布全文核对七章 44 条＋申请文件目录附件；含与 26 号准则的 7 项关键差异速查（报告期、财务资料有效期 6+1 个月、重组上市引 46 号准则、尾页声明等）；内置 2026-07 征求意见稿（第三十二条拟改 3 个月）未落地的核验门禁。

**修正（按 26 号准则 2023-02-17 公布、2023-10-27 修正版原文逐条比对）**
- `references/rule26-checklist.md`：修复 6 处条款错配——重大事项提示改挂第十一条（原误挂第十条"释义"）、重大风险提示改挂第十二条（原误挂第十一条）、第五十四条实为立案调查锁定承诺（原误作"证券服务机构声明"，并加注中介报告属申请文件第四章）、删除 2023 版已取消的"交易前后主要财务数据对比"行（原误挂第四十条）、同业竞争改挂第四十条（原误挂第四十六条治理机制）、重组上市特别要求按第五十五条原文重写（引 57 号准则，原误引"26 号准则第七十八条"）；版本基线写入精确版本；补充第九条目录、第十条释义检查项。
- `references/rule26-checklist.md` C 节：北交所由 NOT_IN_SCOPE 改为路由至 56 号准则逐条清单；删除三处未能证实的业务指引要点（停牌 10 日、媒体说明会、6 个月专项说明）。

**兼容迁移**
- `assets/review-manifest.schema.json`：`authority_baseline` 条目改 oneOf（对象 + 旧字符串），兼容历史项目 manifest。
- `scripts/validate_review_artifacts.py`：对旧字符串条目逐条发迁移警告，并说明其不参与权威来源挂载核对。
- `references/review-charter.md`：新增"旧格式迁移"段，要求续核历史项目先迁移为 `{data_type, source_ref, note}` 对象格式。

**文字统一**
- "发行人"→"标的公司"共 4 处（`error-taxonomy.md`、`delivery-and-traceability.md`、`external-check.md` 两处）；`rule26-checklist.md` 中《57 号准则》章节名"发行人基本情况"属法规原文引用，保留未改。

**长文档策略强化**（`references/long-doc-strategy.md`）
- 长文档阈值参数化：安全装载量 ≈ 实际上下文窗口 × 60%，不再写死 40 万字符（保留历史默认值作兜底）。
- 新增"定性事实索引"机制（qualitative-facts.jsonl）：控制权认定、承诺事项、口径定义、关键日期/比例、主体全称跨章对碰；未建索引的项目元审计不得整体记 COMPLETE。
- 数值索引明确必须覆盖正文文字中的数值（不只表格）。
- 新增"最低检查集"硬规则：所有章节（含低优先级定性章节）必须完成程序化六件套＋表外一致＋索引抽取，未完成不得记 COMPLETE。

**自测**：校验脚本 4 个用例全过（含新增 legacy 字符串条目用例）。

## 3.1.0（2026-09-26）

适用范围收窄为并购重组申报文件（不再覆盖 IPO/再融资）。

- `SKILL.md`：描述与路由收窄至重大资产重组、发行股份购买资产、重组上市等；新增门禁与路由规则。
- 新增 `references/deal-arithmetic.md`（发行方案与业绩承诺复算）、`references/workpaper-tracing.md`（底稿穿透）。
- `table-arithmetic.md`/`cross-file-check.md`/`extension-review.md`：阈值参数化、加期口径、反向对碰。
- `review-charter.md`/`external-check.md`/`delivery-and-traceability.md`/`error-taxonomy.md`/`meta-audit.md`/schema/validator 同步修改。
- 历史项目示例统一标注"仅说明方法，不得当作当前任务事实"；清理项目残留。
- 校验脚本自测 3 个用例全过。
