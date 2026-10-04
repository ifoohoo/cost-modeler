# -*- coding: utf-8 -*-
"""语义候选。只筛行，不下判不过。"""
from __future__ import annotations

import re

from .load import WorkbookData
from .textutil import query_spans

ENGLISH = re.compile(r"[A-Za-z][A-Za-z0-9_]{1,}")
PATH = re.compile(r"/[A-Za-z0-9_\-./]+")


def _add(items, sheet, row, column, content, kind):
    text = content if len(content) <= 180 else content[:180] + "…"
    items.append({"表名": sheet, "行号": row, "列名": column, "内容": text, "疑点类别": kind})


def _business(items, sheet, row, column, content):
    if not content or content == "—":
        return
    if ENGLISH.search(content) or PATH.search(content):
        _add(items, sheet, row, column, content, "业务语义红线")


def _affirmative_labels(span: str) -> int:
    """查询结果里完整的肯定标签。子串、否定和说不准的说法不算。"""
    text = span.replace("`", "")
    found = 0
    for matched in re.finditer(r"沿用通用字典|沿用通用参数", text):
        previous = text[matched.start() - 1] if matched.start() else ""
        following = text[matched.end():matched.end() + 1]
        if previous not in ("", "为", "，", "。", "：", "；"):
            continue
        if following not in ("", "；", "，", "。", "："):
            continue
        if previous == "为":
            before = text[max(0, matched.start() - 3):matched.start() - 1]
            if before.endswith("不") or before.endswith("是否"):
                continue
        found += 1
    return found


def collect(book: WorkbookData) -> list[dict]:
    items = []
    for rec in book.logical("表A"):
        for column in ("活动名称", "输入", "输出"):
            _business(items, rec.sheet, rec.row, column, rec.get(column, ""))
    for rec in book.logical("表B"):
        for column in ("输出：业务对象 + 完成后的状态", "输入：业务对象 + 进入时的状态"):
            _business(items, rec.sheet, rec.row, column, rec.get(column, ""))
    for rec in book.logical("补登"):
        _business(items, rec.sheet, rec.row, "候选活动名称", rec.get("候选活动名称", ""))
    for rec in book.logical("机能"):
        matched = re.search(r"区块业务目的：([^；]*)", rec.get("来源证据", ""))
        if not matched:
            continue
        purpose = matched.group(1).strip()
        _business(items, rec.sheet, rec.row, "来源证据", purpose)
        if purpose in ("", "—") or len(purpose) < 4:
            _add(items, rec.sheet, rec.row, "来源证据", purpose, "证据叙述不清")
    for rec in book.logical("功能"):
        evidence = rec.get("来源证据", "")
        matched = re.search(r"非业务功能理由：([^；]*)", evidence)
        if matched and len(matched.group(1).strip()) < 8:
            _add(items, rec.sheet, rec.row, "来源证据", matched.group(1).strip(), "证据叙述不清")
        for span in query_spans(evidence):
            if span.count("沿用") > _affirmative_labels(span):
                _add(items, rec.sheet, rec.row, "来源证据", evidence, "沿用措辞含糊")
                break
    return items
