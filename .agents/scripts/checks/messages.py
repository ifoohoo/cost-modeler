# -*- coding: utf-8 -*-
"""第六节违规句。占位照填，其余文字不改。"""
from __future__ import annotations

from pathlib import Path

from .model import CHECK_NAME
from .report_text import phrase
from .sections import load_sections

_FINDINGS = load_sections(Path(__file__).resolve().parents[2] / "references" / "发现句.md")


def line(code: str, body: str) -> str:
    return f"【{code}｜{CHECK_NAME[code]}】{body}"


def say(key: str, /, **kwargs: object) -> str:
    """取出一条发现句。占位符只填格子里的原值。"""
    try:
        template = _FINDINGS[key]
    except KeyError as exc:
        raise KeyError(key) from exc
    if not template:
        raise KeyError(key)
    return template.format(**kwargs)


def na_line(code: str, obj: str) -> str:
    return phrase("na_line").format(code=code, name=CHECK_NAME[code], obj=obj)
