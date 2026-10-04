# -*- coding: utf-8 -*-
"""环境检查。只检查，不安装，不改文件。"""
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
    parser = argparse.ArgumentParser(description="检查成本表技能族的运行环境")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    result = diagnose(args.root)
    for item in result["checks"]:
        mark = "过" if item["ok"] else "缺"
        print(f"{mark} {item['name']}：{item['detail']}")
    if result["ready"]:
        print("就绪。这一步不安装，也不改文件。")
        return 0
    print("还没就绪。下面是计划，本脚本不执行它。要做的话，先明确同意再按计划做。")
    for index, step in enumerate(result["plan"], start=1):
        print(f"{index}. {step}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
