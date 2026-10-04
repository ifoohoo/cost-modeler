---
name: cost-modeler-help
description: 说明成本核算表格技能族能做哪两件事、各自停在哪里，以及该去哪个入口。
user-invocable: true
---

# 成本核算表格技能族说明

已加载的 `SKILL.md` 位于 `skills/<入口名>/SKILL.md`，包根是 `skills/` 的上一级目录。下文用 `<plugin-root>`（即命令中的 `〈包根〉`）表示这个真实包根；使用前从当前加载的技能路径确定它，并替换为实际绝对路径，不把它当作系统已有环境变量。共享脚本是 `<plugin-root>/scripts/validate.py` 和 `<plugin-root>/scripts/fill_guide.py`；docs、references、templates 和 examples 是同一包根下的目录。用户工作簿、`.venv` 和报告仍写在业务目录。不要把当前工作目录当成包根，也不要使用开发机上的固定绝对路径。


这个族做两件事。

- 检查：读一份按《成本核算表格模板》填好的工作簿，用 `validate.py` 从 V-00 到 V-42 出报告。结论是「通过」、「判不过」或「无法出结论」。预警、无法校验、不适用另列。判定、编号和金额由检查程序决定。
- 填写引导：人点名一张表的一行，或还不会填时，走 `cost-modeler-fill`。先检索文稿，再顺着文稿写明的关联读对应行，一次只问一句还缺的现场事实，并写入已经推出的空格子。

说明入口有三个：本说明、环境检查 `cost-modeler-setup`，以及不确定该用哪个时的 `cost-modeler-quickstart`。两项工作的入口是 `cost-modeler-validate`（检查）和 `cost-modeler-fill`（填写引导）。熟悉之后可以直接去这两个入口。

## 依赖和最小例子

跑检查或填写，需要项目根目录下的 `.venv`，并且这个环境能导入 openpyxl。环境不齐时去 `cost-modeler-setup`。它只检查并给出计划，未经同意不安装，也不因为有新版本就更换已经能用的 openpyxl。

检查一份工作簿：

```bash
〈业务目录〉/.venv/bin/python 〈包根〉/scripts/validate.py 〈工作簿.xlsx〉 -o 〈业务目录〉/work/cost-modeler/报告.md
```

填写某一行时，打开 `cost-modeler-fill`，按那里的检索回合做。读取指定行：

```bash
〈业务目录〉/.venv/bin/python 〈包根〉/scripts/fill_guide.py --dump --workbook 〈工作簿.xlsx〉 --sheet 〈表名〉 --row 〈行号〉
```

命令失败、找不到解释器，或 openpyxl 导入失败时，先看 setup 打出的缺项。不知道该检查还是填写时，用 quickstart，由它说明差别。工作簿和报告只在本机读写，本入口不把表格发到别处。

## 能力边界

本入口只作说明，不读工作簿，不改文件，不安装，不联网。

检查不改工作簿。填写引导不写表 A、说明、整页由机器生成的表和链路核对视图，不覆盖已经写过的格子，也不代替检查下结论。这两件事都不调用别的技能。

各入口的范围见 `<plugin-root>/references/能力边界.md`。填写怎么检索、怎么问、怎么写，见 `cost-modeler-fill`。
