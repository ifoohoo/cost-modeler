# -*- coding: utf-8 -*-
"""V-00 模版结构、V-01 表头一致。表头不合格或分不清示例区的表，不再读入数据行。"""
from __future__ import annotations

from .load import WorkbookData
from .messages import line, say
from .model import HEADERS, TABLE_A_GROUP, TABLE_A_HEAD, TABLE_A_INFO, TABLE_A_SHEET, TABLE_A_TAIL, TEMPLATE_SHEETS, Sink

STRUCTURAL_EXTRA = ("全局活动清单", "已结期次留存副本", "全系统成本恒等式")


def _expected(name: str):
    if name == TABLE_A_SHEET:
        return None
    if name in HEADERS:
        return HEADERS[name]
    if name.startswith("分摊表"):
        return HEADERS["分摊表"]
    if name.startswith("成本恒等式") or name == "全系统成本恒等式":
        return HEADERS["成本恒等式"]
    return None


def _names(book: WorkbookData) -> list[str]:
    names = list(TEMPLATE_SHEETS)
    for name in book.tables:
        if name not in names and _expected(name):
            if name.startswith("分摊表·") or name.startswith("成本恒等式·") or name in STRUCTURAL_EXTRA:
                names.append(name)
    return names


def _column_fail(sink: Sink, name: str, index: int, want: str, got: str) -> None:
    sink.add_fail("V-01", line(
        "V-01",
        say("l0_structure.V-01.1", p0=name, p1=index, p2=(want or '（无此列）'), p3=(got or '（空）')),
    ))


def _group_fail(sink: Sink, problem: str) -> None:
    sink.add_fail("V-01", line(
        "V-01",
        say("l0_structure.V-01.2", p0=problem),
    ))


def _table_a(book: WorkbookData, sink: Sink, table) -> None:
    """表 A 专项：固定信息列 11 列逐字，分组行能找到「角色分工」，角色列列头非空且不重复。"""
    headers = table.headers
    width = len(headers)
    bad = False
    if not table.role_group_found:
        _group_fail(sink, say("frag.001"))
        bad = True
        role_cols = list(range(TABLE_A_HEAD + 1, max(TABLE_A_HEAD + 1, width - TABLE_A_TAIL + 1)))
    else:
        role_cols = list(table.role_cols)
    head = list(range(1, TABLE_A_HEAD + 1))
    tail = list(range((role_cols[-1] if role_cols else TABLE_A_HEAD) + 1, width + 1))
    for index in head:
        want = TABLE_A_INFO[index - 1]
        got = headers[index - 1] if index <= width else ""
        if got != want:
            _column_fail(sink, TABLE_A_SHEET, index, want, got)
            bad = True
    for offset, index in enumerate(tail):
        want = TABLE_A_INFO[TABLE_A_HEAD + offset] if TABLE_A_HEAD + offset < len(TABLE_A_INFO) else ""
        got = headers[index - 1]
        if got != want:
            _column_fail(sink, TABLE_A_SHEET, index, want, got)
            bad = True
    missing = len(TABLE_A_INFO) - TABLE_A_HEAD - len(tail)
    if missing > 0:
        for offset in range(len(tail), len(TABLE_A_INFO) - TABLE_A_HEAD):
            _column_fail(sink, TABLE_A_SHEET, (role_cols[-1] if role_cols else TABLE_A_HEAD) + offset + 1, TABLE_A_INFO[TABLE_A_HEAD + offset], "")
            bad = True
    seen = set()
    for col in role_cols:
        name = headers[col - 1] if col <= width else ""
        if name == "":
            _group_fail(sink, say("frag.002", p0=col))
            bad = True
        elif name in seen:
            _group_fail(sink, say("frag.003", p0=name))
            bad = True
        else:
            seen.add(name)
    if bad:
        sink.add_fail("V-01", say("l0_structure.V-01.header_stop", p0=TABLE_A_SHEET))
        table.header_bad = True
        table.rows = []
        book.by_logical["表A"] = []


def run(book: WorkbookData, sink: Sink) -> None:
    for name in TEMPLATE_SHEETS:
        table = book.tables.get(name)
        if table is None or not table.present:
            sink.add_fail("V-00", line(
                "V-00",
                say("l0_structure.V-00.2", p0=name),
            ))
    for name, table in book.tables.items():
        if not table.present or not table.separator_missing:
            continue
        if name in ("说明", "整页级份额（机器执行）"):
            continue
        sink.add_fail("V-00", line(
            "V-00",
            say("l0_structure.V-00.1", p0=name),
        ))

    table_a = book.tables.get(TABLE_A_SHEET)
    if table_a is not None and table_a.present and not table_a.separator_missing:
        _table_a(book, sink, table_a)

    for name in _names(book):
        if name == TABLE_A_SHEET:
            continue
        table = book.tables.get(name)
        if table is None or not table.present:
            continue
        expected = _expected(name)
        if not expected:
            continue
        actual = table.headers
        bad = False
        width = max(len(expected), len(actual))
        for index in range(width):
            want = expected[index] if index < len(expected) else ""
            got = actual[index] if index < len(actual) else ""
            if want == got:
                continue
            bad = True
            _column_fail(sink, name, index + 1, want, got)
        if bad:
            sink.add_fail("V-01", say("l0_structure.V-01.header_stop", p0=name))
            table.header_bad = True
            table.rows = []
