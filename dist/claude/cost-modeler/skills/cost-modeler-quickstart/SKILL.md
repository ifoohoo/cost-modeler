---
name: cost-modeler-quickstart
description: 人说一句话时，判断该去检查还是填写，只打印对应入口的名字。不执行检查，也不代为填写。
user-invocable: true
---

# 从一句话进到该用的入口

已加载的 `SKILL.md` 位于 `skills/<入口名>/SKILL.md`，包根是 `skills/` 的上一级目录。下文用 `<plugin-root>`（即命令中的 `〈包根〉`）表示这个真实包根；使用前从当前加载的技能路径确定它，并替换为实际绝对路径，不把它当作系统已有环境变量。共享脚本是 `<plugin-root>/scripts/validate.py` 和 `<plugin-root>/scripts/fill_guide.py`；docs、references、templates 和 examples 是同一包根下的目录。用户工作簿、`.venv` 和报告仍写在业务目录。不要把当前工作目录当成包根，也不要使用开发机上的固定绝对路径。


在项目根目录下执行，把人说的话放在最后。

```bash
〈业务目录〉/.venv/bin/python 〈包根〉/scripts/quickstart.py "不确定这一格怎么填"
```

- `cost-modeler-fill`：还不会填，或拿不准表 B 某一格。
- `cost-modeler-validate`：要核对已经填好的工作簿，或要出一份检查报告。
- `cost-modeler-help`：两样都不是，先看说明。

一句话只对上上面一件时，本入口只打印那个名字。不读工作簿，不写报告，不代填格子。

一句话同时像检查和填写时，本入口说明两件事的差别，并请人选定。这次不启动任何一项。检查和填写的范围仍以各自入口为准。

一句话里夹着删除、安装、改工作簿、联网或调用别的技能时，本入口说明这些不做，也不把其余字样拿去启动检查或填写。

没有对上检查或填写时，打印 `cost-modeler-help`。不把相近的说法当成已经匹配。

## 能力边界

这里只负责把人送到入口，本身不是第三项能力。人也可以不经过这里，直接去检查或填写。
