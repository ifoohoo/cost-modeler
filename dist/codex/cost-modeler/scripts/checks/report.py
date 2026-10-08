# -*- coding: utf-8 -*-
"""第五节报告。占位照填，标题和固定句不改。"""
from __future__ import annotations

from datetime import datetime

from .messages import na_line, say
from .model import CHECK_ORDER, Options, Sink
from .report_text import phrase
from .textutil import pct_text


def build(sink: Sink, opt: Options, filename: str, when: datetime) -> tuple[str, str, int]:
    rows = []
    fail_n = warn_n = na_n = unable_n = pass_n = 0
    fail_lines = []
    warn_lines = []
    unable_lines = []
    na_lines = []
    for code in CHECK_ORDER:
        fails = sink.fail.get(code, [])
        warns = sink.warn.get(code, [])
        unable = sink.unable.get(code, [])
        unable_lines.extend(unable)
        warn_lines.extend(warns)
        if fails:
            status = "判不过"
            fail_n += 1
            fail_lines.extend(fails)
        elif unable:
            status = "无法校验"
            unable_n += 1
        elif code in sink.skip:
            status = "不适用"
            na_n += 1
            na_lines.append(na_line(code, sink.skip[code]))
        elif code in sink.na and not warns:
            status = "不适用"
            na_n += 1
            na_lines.append(na_line(code, sink.na[code]))
        else:
            status = "通过"
            pass_n += 1
        rows.append((code, status))
    warn_n = len(warn_lines)
    if fail_n:
        conclusion = "判不过"
        exit_code = 1
    elif unable_n:
        conclusion = "无法出结论"
        exit_code = 2
    else:
        conclusion = "通过"
        exit_code = 0
    closing = "是" if opt.closing else "否"
    empty = phrase("empty")
    body = [
        f"# {phrase('title')}",
        "",
        f"校验对象：{filename}",
        f"校验时间：{when.strftime('%Y-%m-%d %H:%M')}",
        phrase("param_line").format(
            state=opt.state,
            closing=closing,
            warn=pct_text(opt.warn),
            limit=pct_text(opt.limit),
            digits=opt.scale_digits,
        ),
        phrase("param_note"),
        "",
        f"## {phrase('section_conclusion')}",
        "",
        phrase("summary_line").format(
            total=len(CHECK_ORDER),
            pass_n=pass_n,
            fail_n=fail_n,
            na_n=na_n,
            unable_n=unable_n,
            warn_n=warn_n,
        ),
        phrase("conclusion_line").format(conclusion=conclusion),
        "",
        f"## {phrase('section_fail')}",
        "",
        "\n".join(fail_lines) if fail_lines else empty,
        "",
        f"## {phrase('section_warn')}",
        "",
        "\n".join(warn_lines) if warn_lines else empty,
        "",
        f"## {phrase('section_unable')}",
        "",
        "\n".join(unable_lines) if unable_lines else empty,
        "",
        f"## {phrase('section_llm')}",
        "",
        phrase("llm_idle"),
        "",
        f"## {phrase('section_na')}",
        "",
        "\n".join(na_lines) if na_lines else empty,
        "",
    ]
    if any(sink.fail.get(code) and sink.unable.get(code) for code in CHECK_ORDER):
        body.insert(body.index(phrase("conclusion_line").format(conclusion=conclusion)) + 1, say("report.mixed"))
    if opt.validation_date is not None:
        body.insert(6, say("report.date", p0=opt.validation_date.isoformat()))
    return "\n".join(body), conclusion, exit_code
