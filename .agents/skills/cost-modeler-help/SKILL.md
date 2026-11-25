---
name: cost-modeler-help
description: 说明软件成本建模技能族能做哪两项工作、各自的读写边界，以及应当进入哪个入口。
user-invocable: true
---
<!-- @feature CM4 -->

# 软件成本建模技能族说明

若当前加载的 `SKILL.md` 位于 `skills/<入口名>/SKILL.md`，`skills/` 的上一级目录即为真实包根；若从工作区 `.agents/skills/<入口名>/SKILL.md` 加载，`.agents/` 的上一级目录即为真实包根（下文记作 `<plugin-root>` 或命令中的 `〈包根〉`，共享入口为 `<plugin-root>/scripts/validate.py` 与 `<plugin-root>/scripts/fill_guide.py`）。调用共享脚本前，请先从当前 `SKILL.md` 路径推导并替换为真实绝对路径，不要把它当作系统预置环境变量，也不要用当前工作目录代替包根。scripts、docs、references、templates 和 examples 目录均位于包根下；用户工作簿、`.venv` 与报告保存在用户业务目录中。

## 核心能力与入口分工

本技能族围绕《成本核算表格模板（v2）》承担两项业务工作：

- **工作簿校验（`cost-modeler-validate`）**：先运行 `validate.py` 完成 `V-00` 至 `V-42` 的确定规则检查（总体结论分为「通过」「判不过」或「无法出结论」，预警、无法校验与不适用单列，编号和金额均由脚本精确重算），再由当前会话结合方法论完成全量业务语义复核。
- **按事实填写引导（`cost-modeler-fill`）**：针对用户指定的表格与行（或列），先检索方法论文稿并读取关联行，每次只追问一项还缺的现场事实，推导并写入可确定的空白单元格。

除上述两个业务入口外，另提供三个辅助入口：本说明 `cost-modeler-help`、运行环境检查 `cost-modeler-setup`、以及一句话分诊 `cost-modeler-quickstart`。熟悉分工后可直接调用 `cost-modeler-validate` 或 `cost-modeler-fill`。

## 环境依赖与最小命令示例

执行校验或填写引导前，目标业务目录下需具备可导入 `openpyxl` 的 `.venv` 虚拟环境。若环境尚未就绪，可先运行 `cost-modeler-setup`（仅诊断并打印计划，未经明确同意绝不安装，也不会擅自升级已可用的 `openpyxl`）。

只读校验一份工作簿：

```bash
〈业务目录〉/.venv/bin/python 〈包根〉/scripts/validate.py 〈工作簿.xlsx〉 -o 〈业务目录〉/work/cost-modeler/报告.md
```

读取指定行的列名、填写说明与现有内容（配合 `cost-modeler-fill` 流程）：

```bash
〈业务目录〉/.venv/bin/python 〈包根〉/scripts/fill_guide.py --dump --workbook 〈工作簿.xlsx〉 --sheet 〈表名〉 --row 〈行号〉
```

## 语义与安全边界

- 本入口仅提供能力说明，不读取工作簿、不修改文件、不安装依赖、不连接网络。
- 工作簿校验全程只读；填写引导不写 `表 A 活动明细表`、`说明`、`整页级份额（机器执行）` 与 `链路核对视图`，绝不覆盖已有内容，也不替代校验出具验收结论。
- 各入口详细边界见 `<plugin-root>/references/能力边界.md`。
