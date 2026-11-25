# -*- coding: utf-8 -*-
"""环境检查。只检查，不安装，不改文件。

<!-- @feature CM4 -->
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent
PACKAGE = SCRIPT.parent


def diagnose(root: Path | None = None) -> dict:
    root = root or Path.cwd()
    py = root / ".venv" / "bin" / "python"
    checks = []
    interpreter_ok = py.is_file()
    checks.append({
        "name": "解释器",
        "ok": interpreter_ok,
        "detail": str(py) if interpreter_ok else "项目根下没有 .venv/bin/python",
    })
    openpyxl_ok = False
    if interpreter_ok:
        probe = subprocess.run(
            [str(py), "-c", "import openpyxl"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        openpyxl_ok = probe.returncode == 0
    checks.append({
        "name": "openpyxl",
        "ok": openpyxl_ok,
        "detail": "可以导入" if openpyxl_ok else "当前解释器导入 openpyxl 失败",
    })
    entry_ok = (SCRIPT / "validate.py").is_file() and (SCRIPT / "fill_guide.py").is_file()
    checks.append({
        "name": "入口",
        "ok": entry_ok,
        "detail": "validate.py 和 fill_guide.py 都在" if entry_ok else "检查或填写引导入口缺失",
    })
    ready = all(item["ok"] for item in checks)
    plan = []
    if not ready:
        plan = [
            "在项目根保留已有的 .venv；没有才创建，不重建已经有的环境。",
            "用这个环境安装 openpyxl。计划中的命令是：python3 -m venv .venv && .venv/bin/python -m pip install openpyxl",
            "装完再跑一次本脚本。三件事都过才算就绪。",
        ]
    return {"ready": ready, "checks": checks, "plan": plan}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="只读检查软件成本建模技能族在业务目录下的 Python 环境与入口脚本")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="目标业务目录根路径（默认：当前工作目录）")
    args = parser.parse_args(argv)
    result = diagnose(args.root)
    for item in result["checks"]:
        mark = "过" if item["ok"] else "缺"
        print(f"{mark} {item['name']}：{item['detail']}")
    if result["ready"]:
        print("就绪。本次诊断不安装依赖，也不修改任何文件。")
        return 0
    print("环境尚未就绪。以下为准备计划（本脚本只输出计划，请获用户明确同意后再按步骤执行）：")
    for index, step in enumerate(result["plan"], start=1):
        print(f"{index}. {step}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
