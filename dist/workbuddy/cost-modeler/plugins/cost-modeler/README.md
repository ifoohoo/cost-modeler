# 软件成本建模 0.1.0 安装说明

「软件成本建模」（Cost Modeler）的插件名为 `cost-modeler`，版本 `0.1.0`。正式安装与更新从公开发行仓 `ifoohoo/cost-modeler` 走各宿主官方远端入口，跟踪默认分支 `main`。需要固定某一发布时，使用精确标签，首发为 `cost-modeler-v0.1.0`。钉在标签时，宿主更新命令不会自动改到新标签。正式路径不是手工解压 ZIP，也不是自建 marketplace。

五个入口名称固定：

- `cost-modeler-validate`：检查已经填好的工作簿
- `cost-modeler-fill`：按现场事实填写还空着的格子
- `cost-modeler-help`：说明这两类能力停在哪里
- `cost-modeler-setup`：检查业务目录的 Python 环境；得到明确同意后才安装依赖
- `cost-modeler-quickstart`：一句话分诊到上面某个入口

# 首次使用与写入边界

安装后，可以先在会话中提出这个请求：
```text
请调用 cost-modeler-help，说明软件成本建模能做什么、不能做什么，暂不读取或修改工作簿。
```
`cost-modeler-help` 只说明能力，不读取工作簿、不修改文件，也不执行安装或联网工具。上面是会话请求示例，不是终端命令；入口的具体调用方式由宿主决定。宿主大模型对话的数据处理仍遵循所用宿主的政策。

<!-- release-skill:capability:safe-first-command -->

- **`cost-modeler-validate`** 用于检查已填写的工作簿，**不改写已有内容**，生成诊断报告和预筛结果。输出至用户指定的业务目录，不影响原始工作簿。
- **`cost-modeler-fill`** 仅填充空白单元格，**绝不覆盖已有值**，按已确认的现场事实，在用户点名的表格和行范围内执行；事实不足的格子保留空白。
- **`cost-modeler-setup`** 先做环境检查；需要安装时先输出计划。**必须获得用户明确同意后**，才创建或复用 `.venv` 并安装`openpyxl` `3.1.5`；缺少可用 Python 解释器时先说明前提，不承诺自动安装解释器。
- 插件安装与更新由宿主从 GitHub 远端完成，需要联网。

<!-- release-skill:capability:external-write-boundary -->

**故障排查**：

- 若入口未出现，请先核对宿主插件安装状态，并重启会话。
- 若提示缺少 Python 解释器或 `openpyxl==3.1.5`，请调用 `cost-modeler-setup` 检查指定业务目录，根据实际诊断结果获取安装计划，经确认后执行。

五个入口是 `skills/<入口>/SKILL.md`。运行时从实际加载的 `SKILL.md` 确定包根（`skills/` 的上一级），再找 `scripts/`、`docs/`、`references/`、`templates/`、`examples/`。用户工作簿、`.venv` 和校验报告写在业务目录，不写进安装包。只把五个入口文件夹拷进技能根，脚本和文稿会找不到。

业务解释器需要能导入 `openpyxl` `3.1.5`。构建用的 Node 不是填写工作簿的运行时。

| 宿主 | 正常安装（跟踪 `main`） |
|---|---|
| Claude Code | 添加目录 `ifoohoo/cost-modeler`，安装 `cost-modeler@cost-modeler` |
| Grok | `grok plugin install ifoohoo/cost-modeler#dist/claude/cost-modeler` |
| Codex | 添加目录 `ifoohoo/cost-modeler`，安装 `cost-modeler@cost-modeler` |
| WorkBuddy | 插件页添加 `https://github.com/ifoohoo/cost-modeler.git`，安装 `cost-modeler` |

Grok 不在 Foundation `0.23.0` 的 host registry，不另造 `grok` hostId，与 Claude Code 使用同一份包 `dist/claude/cost-modeler/`。本次线上安装与更新流程未实测，不把官方文档或本机帮助写成实测通过。迁移已在 Grok 上实际加载新包完成业务填写，那次验证仍然保留，不表示四宿主安装均已实测。本仓三个目录文件是官方允许的仓库级安装入口，不是向第三方公共插件目录投稿。

# Claude Code

需要已安装 Claude Code。公开仓仓库根提供 `.claude-plugin/marketplace.json`，插件相对路径 `./dist/claude/cost-modeler`。

在会话中添加目录并安装：

```
/plugin marketplace add ifoohoo/cost-modeler
/plugin install cost-modeler@cost-modeler
```

终端等价命令：

```bash
claude plugin marketplace add ifoohoo/cost-modeler
claude plugin install cost-modeler@cost-modeler
```

更新已添加的目录（自动更新默认关闭）：

```
/plugin marketplace update cost-modeler
```

或在终端：

```bash
claude plugin update cost-modeler@cost-modeler
```

官方说明：未开启自动更新时需要手动更新；宿主按插件 `version` 决定是否换成新副本。本包包内 `.claude-plugin/plugin.json` 的 `version` 为 `0.1.0`。固定某一发布时，添加目录写成 `ifoohoo/cost-modeler#cost-modeler-v0.1.0`。

# Grok

与 Claude Code 使用同一份包。本机已核对该帮助的 CLI 为 `1.0.46`。不宣称未核对该组子命令的版本可用。

正常安装：

```bash
grok plugin install ifoohoo/cost-modeler#dist/claude/cost-modeler
```

更新已安装插件：

```bash
grok plugin update cost-modeler
```

固定某一发布：

```bash
grok plugin install ifoohoo/cost-modeler@cost-modeler-v0.1.0#dist/claude/cost-modeler
```

`plugin install` 的 `<SOURCE>` 支持 Git URL、GitHub shorthand `user/repo`、`@ref` 与 `#subdir`。正常路径直接指向公开仓中的 `dist/claude/cost-modeler`。安装后新开会话，入口以 `/cost-modeler-fill` 这类名称出现。

# Codex

兼容范围：本机已核对该帮助的 CLI 为 `codex-cli 0.154.0`。不宣称更早或未核对该组子命令的版本可用。本次线上安装流程未实测。

公开仓仓库根提供 `.agents/plugins/marketplace.json`。`source.path` 相对 marketplace 根，值为 `./dist/codex/cost-modeler`，以 `./` 开头。该目录已有 `.codex-plugin/plugin.json` 以及共享 `skills/`、`scripts/`、`docs/`、`references/`、`templates/`、`examples/`。

正常安装（跟踪 `main`）：

```bash
codex plugin marketplace add ifoohoo/cost-modeler
codex plugin add cost-modeler@cost-modeler
```

刷新已配置源的快照：

```bash
codex plugin marketplace upgrade cost-modeler
```

`upgrade` 只刷新当前已配置 Git 源的快照，不会把已安装插件换成新副本。要从刷新后的目录安装当前插件，再执行：

```bash
codex plugin add cost-modeler@cost-modeler
```

正常路径配置的是 `main`，因此源刷新的是 `main` 上的目录。钉在旧标签时，源刷新仍停在该标签。这是帮助原文推论，不是实测。插件路径已写在目录文件里，添加目录时不加 `--sparse`。

固定某一发布：

```bash
codex plugin marketplace add ifoohoo/cost-modeler --ref cost-modeler-v0.1.0
codex plugin add cost-modeler@cost-modeler
```

`owner/repo@ref` 与 `--ref` 等价，例如 `ifoohoo/cost-modeler@cost-modeler-v0.1.0`。

插件装入后，五入口 `SKILL.md` 在 `skills/<入口>/SKILL.md`，包根为插件根。这是路径推论，不是宿主实测。五个入口需要留在整包的 `skills/` 下，才能找到共享 `scripts/` 与文稿。Foundation 宿主描述仍给出技能根 `.agents/skills` 与 `skill-directory-v1`；那条路径带不走共享包根，正式安装走本节 CLI。

# WorkBuddy

需要已安装 WorkBuddy。公开仓仓库根提供 `.codebuddy-plugin/marketplace.json`，插件相对路径 `./dist/workbuddy/cost-modeler/plugins/cost-modeler`（实际包根，含 `skills/`、`scripts/` 等，不指向 ZIP 外层）。

在插件页面点 +，输入市场地址：

```
https://github.com/ifoohoo/cost-modeler.git
```

浏览并安装 `cost-modeler`。更新走已安装插件管理中的更新。用户已确认该宿主可以添加 GitHub 插件源；本包未做安装实测。

固定某一发布时，在宿主支持的前提下改用精确标签对应的源；本说明不把标签写成界面里尚未核证的必填项。正常路径使用正式发布维护的 `main`。

# 放到宿主之后第一次做业务

装完后，工作簿、虚拟环境和校验报告都在用户自己的业务目录。包根是 `skills/` 的上一级，写作 `〈包根〉`。

在业务目录检查环境：

```bash
〈业务目录〉/.venv/bin/python 〈包根〉/scripts/setup_check.py --root 〈业务目录〉
```

缺解释器或不能导入 `openpyxl` 时，`cost-modeler-setup` 只打印计划，等人明确同意后才在该业务目录创建或复用 `.venv` 并安装 `openpyxl` `3.1.5`。已经能导入的版本保持不动，不因为有新版本就更换。

填写指定表的一行时走 `cost-modeler-fill`；检查已填工作簿走 `cost-modeler-validate`。安装包里的 `templates/成本核算表格模板-v2.xlsx` 用于新表起步；`examples/` 只是随包最小教学案例。不要把开发工作区、规格目录或测试夹具当成日常业务目录。

# 来源、离线附件与未实测

各包插件声明使用同一组身份字段：

```json
{
  "name": "cost-modeler",
  "version": "0.1.0",
  "description": "软件成本建模：成本核算表格校验与按事实填写",
  "skills": "./skills/"
}
```

Foundation `0.23.0` 官方最小插件模板只有 `name`、`version`、`description`；本项目另填 `skills: "./skills/"`。没有 Codex 或 WorkBuddy 的 Foundation 专用模板。宿主描述里的 `hostId` 与技能根用来识别宿主，不是插件模板，也不是远端安装入口。

四个远端安装合同来自各宿主官方入口，补齐 Foundation `0.23.0` 未覆盖处。它们不是 Foundation 模板，也不是向第三方公共插件目录投稿：

1. Claude Code：`https://code.claude.com/docs/en/plugin-marketplaces`
2. Grok：本机 CLI `1.0.46` 的 `plugin install --help` / `plugin update --help`；组合语法为 `owner/repo`、`@ref`、`#subdir`
3. Codex：本机 CLI `codex-cli 0.154.0`；`https://developers.openai.com/codex/plugins/build`，获取 2026-10-04
4. WorkBuddy：`https://www.codebuddy.cn/docs/workbuddy/Plugins`；已安装插件管理见 `https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Plug-In`。目录字段形态参考 CodeBuddy marketplace 说明；WorkBuddy 在界面添加 GitHub 源并安装。

目录 `owner.name` 使用组织 `ifoohoo` 作为目录维护方，不是版权人或许可声明。

三个 ZIP 是同一标签 Release 的可选离线附件，字节对应公开仓中的 `dist/` 目录。ZIP 不是正式安装前提。

| 附件 ZIP | 公开仓中对应目录 | 给谁用 |
|---|---|---|
| `cost-modeler-claude.zip` | `dist/claude/cost-modeler/` | Claude Code；Grok 用同一份 |
| `cost-modeler-codex.zip` | `dist/codex/cost-modeler/` | Codex |
| `cost-modeler-workbuddy.zip` | `dist/workbuddy/cost-modeler/` | WorkBuddy |

WorkBuddy 的 ZIP 顶层仍是旧布局：内层 `.codebuddy-plugin/marketplace.json` 的 `name` 为 `cost-modeler-local`，`owner.name` 为 `private`，`source` 为 `./plugins/cost-modeler`。那是离线附件结构，公开仓目录不使用这组值。
