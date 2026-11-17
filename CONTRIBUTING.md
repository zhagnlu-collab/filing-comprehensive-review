# 参与贡献

感谢参与改进 `filing-comprehensive-review`。本仓库采用“公开提交、维护者审核、通过 Pull Request 合并”的协作方式。

## 可以贡献什么

- 修复文档解析、表格锚定、数字复算或证据台账逻辑。
- 补充跨文件、加期、底稿穿透、问询回复和交易方案复核方法。
- 改进 Word 批注、Excel 问题清单和 HTML 报告的交付规范。
- 增加可复现的脱敏案例、黄金样本和回归测试。
- 更新法规、交易所规则、行业披露要求及外部核验方法。
- 修复文档错漏、安装说明和脚本兼容性问题。

## 协作流程

第一次通过 GitHub 修改本项目的贡献者，请先阅读 [GitHub 修改教程](docs/github-contribution-tutorial.md)。

1. 先在 Issues 或 Discussions 中搜索是否已有相同问题。
2. Fork 本仓库，并从 `main` 创建独立分支：
   - 新功能：`feat/short-description`
   - 缺陷修复：`fix/short-description`
   - 文档修改：`docs/short-description`
3. 完成修改并补充必要文档或测试。
4. 在本地运行验证。
5. 向 `main` 发起 Pull Request，填写变更范围、验证方式和风险。
6. 维护者审核、讨论并合并。

普通贡献者不能直接向主仓库 `main` 推送。维护者也将尽量通过独立分支和 Pull Request 完成变更。

## 本地开发

```bash
git clone https://github.com/<your-account>/filing-comprehensive-review.git
cd filing-comprehensive-review
git remote add upstream https://github.com/zhagnlu-collab/filing-comprehensive-review.git
git switch -c feat/short-description
```

运行仓库结构校验：

```bash
python3 scripts/validate_skill.py
```

如修改了复核方法或交付结构，还应对 `scripts/validate_review_artifacts.py` 和相应 JSON Schema 做最小样例验证。

## 材料与数据安全

本仓库不接受真实项目底稿、未公开交易材料、客户文件或个人信息。

- 提交案例前必须取得授权并完成匿名化、脱敏和删密。
- 不得提交账号密码、Token、Cookie、私钥或内部系统地址。
- 不得在 Issue、PR、日志或测试夹具中披露客户名称、交易金额、证券代码、人员信息或未公开结论。
- 需要说明问题时，请使用虚构数据或最小化、不可反推的结构样例。
- 涉及真实项目的问题，请先按 [SECURITY.md](SECURITY.md) 联系维护者。

## Pull Request 要求

- 一个 PR 尽量只解决一个问题。
- 说明修改前后的行为、影响文件、复核口径和交付格式。
- 业务规则变化必须同步更新 `SKILL.md` 或 `references/`。
- 用户可见变化必须同步更新 `README.md` 和必要的 `CHANGELOG.md`。
- Schema 或交付结构变化必须同步更新 `assets/` 和校验脚本。
- 不得降低证据门禁、把候选事项升级为已确认事实，或删除不可核验记录。
- 不得加入本机绝对路径、缓存、日志、备份或未经授权的二进制文件。
- 提交前运行 `python3 scripts/validate_skill.py`。

## 版本与发布

维护者负责确认版本号、变更日志和主分支合并。贡献者可以在 PR 中建议版本级别，但不应自行发布、覆盖历史提交或强制推送 `main`。

## 许可证说明

本项目采用 [MIT License](LICENSE)。除非另有明确书面约定，提交 Pull Request 即表示同意该贡献按 MIT License 授权并随项目分发。
