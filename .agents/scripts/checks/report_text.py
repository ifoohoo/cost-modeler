# -*- coding: utf-8 -*-
"""报告固定句子。正文在 references/报告模板.md，这里只按名字取出。"""
from __future__ import annotations

from pathlib import Path

from .sections import load_sections

_PATH = Path(__file__).resolve().parents[2] / "references" / "报告模板.md"
_TEXT = load_sections(_PATH)

_REQUIRED = (
    "title",
    "param_note",
    "param_line",
    "summary_line",
    "conclusion_line",
    "section_conclusion",
    "section_fail",
    "section_warn",
    "section_unable",
    "section_llm",
    "section_na",
    "llm_idle",
    "empty",
    "na_line",
)


def phrase(key: str) -> str:
    if key not in _REQUIRED:
        raise KeyError(key)
    value = _TEXT.get(key, "")
    if not value:
        raise KeyError(key)
    return value
