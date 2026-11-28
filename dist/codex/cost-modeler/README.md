# 软件成本建模（Cost Modeler）0.1.6 安装与使用指南

插件标识为 `cost-modeler`（中文名：**软件成本建模**），当前版本 `0.1.6`。正式安装与升级通过公开发行仓库 `ifoohoo/cost-modeler` 的各宿主官方远端入口完成，默认跟踪 `main` 分支；如需锁定特定版本，请指定不可变 Git 标签 `cost-modeler-v0.1.6`（锁定标签后宿主更新命令不会自动切往新标签）。

本技能族固定提供五个入口：

- `cost-modeler-validate`：检查已填写工作簿的填写规范、跨表一致性与业务合理性
- `cost-modeler-fill`：围绕用户指定的表格与行，按现场事实推导并填写空白单元格
- `cost-modeler-help`：说明本技能族的能力范围、入口分工与读写边界
- `cost-modeler-setup`：诊断业务目录的 Python 虚拟环境；仅在获明确同意后安装依赖
- `cost-modeler-quickstart`：将一句话需求分诊到对应入口

## 能力体系与验收边界

`cost-modeler-validate` 覆盖八类检查范围：表格结构与填写规范、跨表引用与登记完整性、业务关联与拆分合理性、功能身份与证据依据、数据移动及规模与复用计量、成本归集与分摊核算、状态历史与关账约束、业务表达与职责清晰度。

- **确定规则与语义复核分层**：先由只读脚本执行结构、必填、引用和金额重算检查，再由当前会话结合方法论与双端正文全量复核活动、功能、机能、计量、原始投入和角色职责。
- **固定报告口径**：报告使用经审核的预置文案并填入真实坐标与必要摘录，分别交代脚本检查范围与模型语义复核范围；正常对象合并列示，同原因资料不足归并定位，不抄录整本表格。
- **通过条件严格受控**：校验全程不修改工作簿。脚本退出码为 `0` 仅代表确定规则通过；只要语义复核未完成、存在语义疑点或缺少必要原始材料，均不能宣称整表通过。

## 首次使用与写入边界

安装完成后，可先在宿主会话中发起如下只读请求了解边界：

```text
请调用 cost-modeler-help，说明软件成本建模能做什么、不能做什么，暂不读取或修改工作簿。
```

`cost-modeler-help` 仅输出能力说明，不读取工作簿、不改动文件，也不执行安装或联网操作（以上为会话提示示例，具体唤醒语法依所用宿主而定）。

<!-- release-skill:capability:safe-first-command -->

- **`cost-modeler-validate`**：全程只读工作簿，将确定规则报告、`prefilter.json` 与 `association-context.json` 输出到用户指定的业务目录。
- **`cost-modeler-fill`**：仅在用户点名的可写表和行内填写空白单元格，**绝不覆盖已有内容**；条件尚未由同对象同状态事实证实时保留空白。
- **`cost-modeler-setup`**：先检查环境并展示三步计划；**必须经用户明确同意后**，才在业务目录创建或复用 `.venv` 并安装 `openpyxl` `3.1.5`（已可用版本保持不动，缺少系统 Python 解释器时仅提示前提，不代装解释器）。
- 插件自身的安装与更新由宿主从 GitHub 远端拉取，需要网络连接；日常业务校验与填写完全在本机完成。

<!-- release-skill:capability:external-write-boundary -->

**常见故障排查**：

- 若会话中看不到技能入口，请核对宿主插件启用状态并重开会话。
- 若运行脚本提示缺少 Python 解释器或无法导入 `openpyxl==3.1.5`，请对目标业务目录调用 `cost-modeler-setup` 获取环境计划，确认后执行。
- 五个入口位于 `skills/<入口名>/SKILL.md`（工作区自动发现投影位于 `.agents/skills/<入口名>/SKILL.md`）：从 `skills/` 加载时取 `skills/` 上一级作为 `〈包根〉`，从 `.agents/skills/` 加载时取 `.agents/` 上一级作为 `〈包根〉`，以此定位共享的 `scripts/`、`docs/`、`references/`、`templates/` 与 `examples/`；请完整安装插件包，切勿只单独复制 `skills/` 子目录。

## 多宿主安装方式速览

| 宿主环境 | 默认安装方式（跟踪 `main`） |
| --- | --- |
| Claude Code | 添加市场 `ifoohoo/cost-modeler`，安装 `cost-modeler@cost-modeler` |
| Grok | `grok plugin install ifoohoo/cost-modeler#dist/claude/cost-modeler` |
| OpenAI Codex | 添加市场 `ifoohoo/cost-modeler`，安装 `cost-modeler@cost-modeler` |
| WorkBuddy | 插件页添加 `https://github.com/ifoohoo/cost-modeler.git`，安装 `cost-modeler` |
| Google Antigravity | 插件根目录提供 `plugin.json` 与 `.agents/skills/`（克隆或复制到插件目录即用） |

> 说明：Foundation `0.39.2` 宿主注册表已收录 `grok`（预览手动宿主），Grok 与 Claude Code 继续共用已实测通过的 `dist/claude/cost-modeler/` 插件包（其余宿主的线上远端拉取命令按各宿主官方文档与 CLI 帮助整理，公开仓根目录市场清单仅作本仓库安装入口）。Antigravity 同步读取公开仓库根目录 `plugin.json`、`skills/` 与工作区 `.agents/skills/`。

### 1. Claude Code

公开仓库根提供 `.claude-plugin/marketplace.json`（指向 `./dist/claude/cost-modeler`）。在会话或终端中执行：

```bash
claude plugin marketplace add ifoohoo/cost-modeler
claude plugin install cost-modeler@cost-modeler
```

手动刷新与更新（默认未开启自动更新时）：

```bash
claude plugin update cost-modeler@cost-modeler
```

如需锁定版本，添加市场时使用 `ifoohoo/cost-modeler#cost-modeler-v0.1.6`。

### 2. Grok（核对 CLI `1.0.46`）

```bash
# 默认安装与更新
grok plugin install ifoohoo/cost-modeler#dist/claude/cost-modeler
grok plugin update cost-modeler

# 锁定特定发布标签
grok plugin install ifoohoo/cost-modeler@cost-modeler-v0.1.6#dist/claude/cost-modeler
```

安装后新开会话即可使用 `/cost-modeler-fill`、`/cost-modeler-validate` 等入口。

### 3. OpenAI Codex（核对 `codex-cli 0.154.0`）

公开仓库根提供 `.agents/plugins/marketplace.json`（`source.path` 为 `./dist/codex/cost-modeler`，内含 `.codex-plugin/plugin.json` 与完整共享资源，添加市场时无需加 `--sparse`）：

```bash
# 默认安装（跟踪 main）
codex plugin marketplace add ifoohoo/cost-modeler
codex plugin add cost-modeler@cost-modeler

# 刷新源快照并更新已装插件
codex plugin marketplace upgrade cost-modeler
codex plugin add cost-modeler@cost-modeler

# 锁定特定发布标签
codex plugin marketplace add ifoohoo/cost-modeler --ref cost-modeler-v0.1.6
codex plugin add cost-modeler@cost-modeler
```

### 4. WorkBuddy

公开仓库根提供 `.codebuddy-plugin/marketplace.json`（指向实际包根 `./dist/workbuddy/cost-modeler/plugins/cost-modeler`）。在 WorkBuddy 插件页面点击 `+` 添加仓库地址：

```text
https://github.com/ifoohoo/cost-modeler.git
```

随后在列表中安装 `cost-modeler`，后续升级通过已安装插件管理界面执行。

### 5. Google Antigravity

公开仓库根提供官方白名单 `plugin.json`、`skills/` 以及工作区自动发现目录 `.agents/skills/`：

- **全局插件目录安装**：将完整仓库（含根 `plugin.json` 与 `skills/`）克隆或复制到 `~/.gemini/config/plugins/cost-modeler/`，重启会话即可发现五个技能入口。
- **工作区自动发现**：若当前工程目录包含 `.agents/skills/cost-modeler-*/SKILL.md`（同步保留 `scripts/`、`docs/`、`references/`、`templates/` 与 `examples/`），Antigravity 会话会自动发现并加载五个技能。

## 安装后在业务目录开展工作

用户的工作簿、`.venv` 虚拟环境与校验报告均保存在用户自己的业务目录中，不写回插件包目录：

```bash
〈业务目录〉/.venv/bin/python 〈包根〉/scripts/setup_check.py --root 〈业务目录〉
```

新建核算工作簿可从随包模板 `〈包根〉/templates/成本核算表格模板-v2.xlsx` 起步；`〈包根〉/examples/` 仅提供教学演示样本，请勿把开发工作区或测试夹具当作日常业务目录。

## 插件身份与离线 Release 附件

各宿主包共享同一插件身份声明（`owner.name: "ifoohoo"` 仅标识仓库组织）：

```json
{
  "name": "cost-modeler",
  "version": "0.1.6",
  "description": "软件成本建模：成本核算表格校验与按事实填写",
  "skills": "./skills/"
}
```

GitHub Release 同时提供三份与公开仓 `dist/` 字节对应的可选离线压缩包（正常联网安装无需下载 ZIP）：

| 离线附件 | 对应公开仓目录 | 适用宿主 |
| --- | --- | --- |
| `cost-modeler-claude.zip` | `dist/claude/cost-modeler/` | Claude Code、Grok |
| `cost-modeler-codex.zip` | `dist/codex/cost-modeler/` | OpenAI Codex |
| `cost-modeler-workbuddy.zip` | `dist/workbuddy/cost-modeler/` | WorkBuddy（离线包内层含本地 `cost-modeler-local` 清单） |
