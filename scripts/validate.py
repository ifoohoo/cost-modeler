# -*- coding: utf-8 -*-
"""成本核算表格校验入口。

用法：
  .venv/bin/python scripts/validate.py 〈工作簿.xlsx〉 \\
    [--状态 正常态|初始化态] [--关账] [--校验日 YYYY-MM-DD] \\
    [--预警值 0.10] [--上限 0.15] [--小数位 4] \\
    [--机器导出名录 〈目录〉] [--上一版表A 〈文件〉] [--已结期次副本 〈文件〉] \\
    [-o 〈报告路径.md〉]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
import re
from decimal import Decimal
from pathlib import Path

from checks import l0_structure, l1_row, l2_ref, l3_recalc, prefilter
from checks.load import load_catalog, load_copy, load_previous, load_workbook_file
from checks.model import Options, Sink
from checks.messages import say
from checks.report import build

ROOT = Path(__file__).resolve().parent


def _validation_date(value: str) -> date:
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(say("cli.date")) from None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验一份成本核算表格工作簿")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--状态", default="正常态", choices=("正常态", "初始化态"))
    parser.add_argument("--关账", action="store_true")
    parser.add_argument("--校验日", type=_validation_date, help=say("cli.date_help"))
    parser.add_argument("--预警值", type=Decimal, default=Decimal("0.10"))
    parser.add_argument("--上限", type=Decimal, default=Decimal("0.15"))
    parser.add_argument("--小数位", type=int, default=4)
    parser.add_argument("--机器导出名录", type=Path)
    parser.add_argument("--上一版表A", type=Path)
    parser.add_argument("--已结期次副本", type=Path)
    parser.add_argument("-o", type=Path)
    return parser.parse_args(argv)


def execute(args: argparse.Namespace, when: datetime | None = None) -> tuple[str, str, int, list[dict]]:
    report, conclusion, exit_code, candidates, _context = _execute(args, when)
    return report, conclusion, exit_code, candidates


def _execute(args: argparse.Namespace, when: datetime | None = None) -> tuple[str, str, int, list[dict], dict]:
    opt = Options(
        state=args.状态,
        closing=bool(args.关账),
        warn=args.预警值,
        limit=args.上限,
        scale_digits=args.小数位,
        validation_date=args.校验日,
    )
    book = load_workbook_file(args.workbook)
    load_previous(args.上一版表A, book)
    load_copy(args.已结期次副本, book)
    load_catalog(args.机器导出名录, book)
    sink = Sink()
    l0_structure.run(book, sink)
    l1_row.run(book, sink, opt)
    l2_ref.run(book, sink)
    l3_recalc.run(book, sink, opt)
    candidates = prefilter.collect(book)
    context = prefilter.association_context(book)
    context["工作簿"] = str(args.workbook.resolve())
    context["校验参数"] = {"状态": opt.state, "关账": opt.closing, "校验日": opt.validation_date.isoformat() if opt.validation_date else None, "小数位": opt.scale_digits}
    report, conclusion, exit_code = build(sink, opt, args.workbook.name, when or datetime.now())
    context["确定规则结论"] = conclusion
    return report, conclusion, exit_code, candidates, context


def main(argv: list[str] | None = None) -> int:
    if __package__ in (None, ""):
        sys.path.insert(0, str(ROOT))
    args = parse_args(argv)
    report, _conclusion, exit_code, candidates, context = _execute(args)
    if args.o:
        args.o.parent.mkdir(parents=True, exist_ok=True)
        args.o.write_text(report, encoding="utf-8")
        prefilter_path = args.o.with_name("prefilter.json")
    else:
        sys.stdout.write(report)
        if not report.endswith("\n"):
            sys.stdout.write("\n")
        prefilter_path = Path("prefilter.json")
    prefilter_path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    context_path = prefilter_path.with_name("association-context.json")
    context_path.write_text(json.dumps(context, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
