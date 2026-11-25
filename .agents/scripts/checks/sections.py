# -*- coding: utf-8 -*-
"""读取技能内按二级标题分节的预设文字。"""
from __future__ import annotations

from pathlib import Path


def load_sections(path: Path) -> dict[str, str]:
    """把 Markdown 的二级标题收成字典。标题下正文去掉首尾空白。"""
    sections: dict[str, str] = {}
    key: str | None = None
    buf: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if key is not None:
                sections[key] = "\n".join(buf).strip()
            key = line[3:].strip()
            buf = []
            continue
        if key is not None:
            buf.append(line)
    if key is not None:
        sections[key] = "\n".join(buf).strip()
    return sections
