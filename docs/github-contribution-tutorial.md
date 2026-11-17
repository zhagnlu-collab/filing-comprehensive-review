# 如何修改 `filing-comprehensive-review`

本教程面向第一次通过 GitHub 参与本 Skill 修改的人。你可以选择：

- **网页版修改**：适合改错别字、文档措辞或少量说明。
- **本地 Fork 修改**：适合改规则、脚本、Schema、测试或多个文件。

本项目采用维护者审核模式。普通贡献者不能直接修改 `zhagnlu-collab/filing-comprehensive-review` 的 `main` 分支，正确流程是：

```text
Fork 仓库 → 新建分支 → 修改 → 本地校验 → 提交 commit → 推送分支 → 发起 Pull Request → 审核合并
```

## 一、先理解权限

| 角色 | 可以做什么 |
| --- | --- |
| 普通 GitHub 用户 | 查看、Fork、在自己 Fork 中修改、发起 Pull Request |
| Collaborator / 维护者 | 可向主仓库推送分支，但 `main` 仍受保护 |
| 仓库所有者 | 审核和合并 PR；管理员保留紧急绕过保护设置的权限 |

不要尝试直接向主仓库 `main` 推送。即使命令暂时可用，也应通过独立分支和 PR 保留审核记录。

## 二、方式一：网页版修改

适用于只改 `README.md`、`SKILL.md` 或 `references/` 中的少量文字。

### 1. Fork 仓库

打开：

`https://github.com/zhagnlu-collab/filing-comprehensive-review`

点击右上角 **Fork**，在你的账号下创建一个副本。

### 2. 在 Fork 中编辑文件

1. 打开你账号下的 `filing-comprehensive-review` Fork。
2. 进入要修改的文件，例如 `README.md`。
3. 点击右上角铅笔图标 **Edit this file**。
4. 修改内容后，在页面底部选择 **Create a new branch for this commit and start a pull request**。
5. 分支名示例：
   - `docs/fix-readme`
   - `docs/update-mcp-guide`
   - `fix/typo-in-skill`
6. 点击 **Propose changes**。

### 3. 发起 Pull Request

进入 Pull Request 页面，确认：

- Base repository：`zhagnlu-collab/filing-comprehensive-review`
- Base branch：`main`
- Head repository：你的 Fork
- Head branch：刚创建的分支

填写标题、修改原因和验证方式，然后点击 **Create pull request**。

## 三、方式二：本地 Fork 修改（推荐）

适用于修改脚本、规则、Schema、多个文档或需要运行测试的变更。

### 0. 准备环境

确认已安装：

```bash
git --version
python3 --version
```

建议使用 Python 3.12 左右版本。安装常用依赖：

```bash
python3 -m pip install openpyxl python-docx python-pptx pypdf lxml
```

不熟悉命令行的用户也可以使用 GitHub Desktop、VS Code 或 JetBrains 客户端完成 Fork、克隆、分支、提交和推送。

### 1. Fork 仓库

打开 `https://github.com/zhagnlu-collab/filing-comprehensive-review`，点击 **Fork**。

### 2. 克隆自己的 Fork

```bash
git clone https://github.com/<你的GitHub用户名>/filing-comprehensive-review.git
cd filing-comprehensive-review
```

### 3. 添加上游仓库

```bash
git remote add upstream https://github.com/zhagnlu-collab/filing-comprehensive-review.git
git remote -v
```

预期：

- `origin` 指向你的 Fork；
- `upstream` 指向 `zhagnlu-collab/filing-comprehensive-review`。

### 4. 同步 `main`

```bash
git fetch upstream
git switch main
git merge --ff-only upstream/main
git push origin main
```

### 5. 新建工作分支

不要直接在自己的 `main` 上修改：

```bash
git switch -c docs/improve-contribution-guide
```

推荐命名：

| 类型 | 示例 |
| --- | --- |
| 文档 | `docs/fix-typo` |
| 缺陷 | `fix/validate-json` |
| 功能 | `feat/add-source-check` |
| 规则口径 | `rule/update-disclosure-check` |
| 测试 | `test/add-regression-case` |

### 6. 修改文件

建议先阅读：

- `README.md`：用户入口和安装说明；
- `SKILL.md`：主流程、边界和规则路由；
- `CONTRIBUTING.md`：提交要求和数据安全规则；
- `references/`：各专项的详细规则；
- `scripts/validate_skill.py`：基础结构校验。

`SKILL.md` 定义复核流程，`references/` 承载详细方法，`assets/` 保存 Schema，规则或交付结构变化必须同步校验脚本。

规则变化应说明旧规则、新规则、适用边界和可能受影响的交付物。不要只改一句话而不更新相关引用文件。

### 7. 运行校验

```bash
python3 scripts/validate_skill.py
```

如果修改了业务脚本，还应：

```bash
python3 -m py_compile scripts/*.py
```

如仓库存在其他测试或产物校验脚本，请一并运行，并在 PR 中如实写明哪些测试已执行、哪些因缺少材料或权限未执行。

### 8. 提交并推送

```bash
git status
git diff
git add <修改的文件>
git commit -m "docs: describe the change"
git push -u origin docs/improve-contribution-guide
```

提交信息建议：

```text
docs: clarify MCP installation
fix: correct validation error handling
feat: add exchange project status check
rule: update disclosure completeness criteria
test: add regression sample for table anchoring
```

### 9. 发起 Pull Request

推送后，GitHub 通常会在仓库页面显示 **Compare & pull request**。也可以手动进入：

`https://github.com/zhagnlu-collab/filing-comprehensive-review/compare`

确认：

- 目标分支为 `zhagnlu-collab/filing-comprehensive-review:main`
- 来源分支为你的 Fork 分支
- 不包含无关文件、缓存、日志或真实项目材料

PR 描述至少写明：

1. 要解决的问题；
2. 修改了哪些文件；
3. 业务口径或行为是否变化；
4. 执行了哪些验证；
5. 还有哪些待确认事项。

### 10. 处理审核意见

维护者可能要求：

- 缩小 PR 范围；
- 增加测试或脱敏样例；
- 补充规则依据；
- 修正文档引用；
- 解决 Markdown、Python 或 YAML 校验错误。

继续在当前分支修改即可：

```bash
git add <修改的文件>
git commit -m "fix: address review comments"
git push
```

PR 会自动更新，不需要重新创建。

## 四、修改内容放哪里

| 修改类型 | 主要位置 |
| --- | --- |
| 使用说明、安装、MCP 配置 | `README.md` |
| 主流程、适用范围、强制规则 | `SKILL.md` |
| 详细业务口径和方法 | `references/` |
| 数据结构与交付 Schema | `assets/`（如仓库有） |
| 自动化与校验 | `scripts/` |
| 贡献流程和数据安全 | `CONTRIBUTING.md`、`SECURITY.md` |
| 版本与历史变化 | `CHANGELOG.md`（如仓库有） |

一个 PR 尽量只做一类修改。不要把重命名、格式化、规则调整和功能开发混在一起。

## 五、数据与安全要求

真实项目底稿、客户资料、未公开交易信息、个人信息和内部系统地址均不得提交。示例必须使用虚构数据或不可反推的脱敏片段。

提交前检查：

```bash
git status
git diff --cached
```

确认没有：

- 密码、Token、Cookie、API Key 或私钥；
- 客户资料、未公开交易信息或个人敏感信息；
- 本机绝对路径、内部系统地址或未脱敏日志；
- `__pycache__`、`.DS_Store`、备份文件或临时输出。

## 六、常见问题

### 1. `Permission denied` 或 `403`

通常是把修改推送到了上游仓库，而不是自己的 Fork。检查：

```bash
git remote -v
```

应推送到 `origin`，即你自己的 Fork。

### 2. 无法直接提交到 `main`

`main` 受分支保护。请新建分支并提交 Pull Request。

### 3. `validate_skill.py` 失败

按错误信息定位文件。常见原因：

- Markdown 本地链接指向不存在的文件；
- JSON 或 YAML 格式错误；
- Python 语法错误；
- 出现本机绝对路径或疑似密钥。

修复后重新运行：

```bash
python3 scripts/validate_skill.py
```

### 4. 上游已经有新提交

```bash
git fetch upstream
git switch main
git merge --ff-only upstream/main
git push origin main
git switch docs/improve-contribution-guide
git rebase main
git push --force-with-lease
```

只对自己的功能分支使用 `--force-with-lease`，不要强制推送 `main`。

### 5. PR 显示很多无关文件

通常是分支从旧版本创建，或混入了本地临时文件。先同步上游 `main`，再检查：

```bash
git diff --stat upstream/main...HEAD
```

必要时重新从最新 `upstream/main` 创建干净分支。

### 6. GitHub Actions 没有立即运行

先等待几分钟，再查看仓库 **Actions** 页面。若仍无记录，检查 `.github/workflows/validate.yml` 是否被 PR 修改或禁用，并在 PR 中说明。

## 七、合并条件

一个可以合并的 PR 通常需要：

- 目标为 `main`；
- `validate` 检查通过；
- 至少一名维护者审核；
- CODEOWNER 审核通过；
- 所有对话已解决；
- 没有强制推送、敏感信息或无关文件；
- 文档、规则、Schema 和测试保持同步。

维护者可以根据变更风险要求补充更多验证。审核通过并不代表贡献内容自动成为机构官方口径，正式使用仍应回到原文和权威来源核验。

## 八、最短流程速查

```bash
# 1. Fork 后克隆
git clone https://github.com/<你的用户名>/filing-comprehensive-review.git
cd filing-comprehensive-review

# 2. 添加并同步上游
git remote add upstream https://github.com/zhagnlu-collab/filing-comprehensive-review.git
git fetch upstream
git switch main
git merge --ff-only upstream/main

# 3. 新建分支
git switch -c docs/my-change

# 4. 修改后校验
python3 scripts/validate_skill.py

# 5. 提交并推送
git add <修改的文件>
git commit -m "docs: explain my change"
git push -u origin docs/my-change

# 6. 在 GitHub 页面发起 Pull Request
```
