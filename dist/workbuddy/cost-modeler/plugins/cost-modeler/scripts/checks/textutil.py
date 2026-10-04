# -*- coding: utf-8 -*-
"""单元格解析。判定口径按附录 D，不另造分支。"""
from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

from .messages import say
from .model import DASH, SEG_TYPE

MONEY = re.compile(r"\d+\.\d{2}")
L4_TOKEN = r"[^\s；、]+"
OWN_L4 = re.compile(rf"主归属 L4：({L4_TOKEN})")
REF_LINE = re.compile(rf"^主归属 L4：{L4_TOKEN}(?:；引用 L4：{L4_TOKEN}(?:、{L4_TOKEN})*)?$")
F_CODE = re.compile(r"F-[A-Za-z0-9.\-]+")
PREFIXES = (
    "非业务功能理由", "专属剥离", "白名单", "对象清单", "P1-①", "P1-②",
    "未另行开发", "使用系统", "依据", "同期证据", "独立责任方", "变更记录编号", "认定依据",
)
MARK_TAIL = re.compile(r"（(?:多调用方，进归挂池|多入口，[^（）；]*)）$")


def unkey(value) -> str:
    text = "" if value is None else str(value).strip()
    if len(text) >= 2 and text[0] == "`" and text[-1] == "`" and "`" not in text[1:-1]:
        return text[1:-1]
    return text


def D(value):
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return None


def rq(value: Decimal, quantum: Decimal) -> Decimal:
    return value.quantize(quantum, rounding=ROUND_HALF_UP)


def fset(value) -> list[str]:
    if value in (DASH, "", None):
        return []
    return [part.strip() for part in str(value).split("；") if part.strip()]


def tailval(evidence) -> Decimal | None:
    matched = re.search(r"尾差：([+\-−]?[\d.]+)", evidence or "")
    if not matched:
        return None
    return D(matched.group(1).replace("−", "-"))


def callers(evidence) -> list[str]:
    if "随调用方：" not in (evidence or ""):
        return []
    segment = evidence.split("随调用方：", 1)[1]
    return [item for item in re.findall(r"`([^`]+)`", segment)]


def own_l4(value) -> str | None:
    matched = OWN_L4.match(value or "")
    return matched.group(1) if matched else None


def ref_l4s(value) -> list[str]:
    matched = re.fullmatch(rf"主归属 L4：{L4_TOKEN}(?:；引用 L4：(.+))?", value or "")
    if not matched or not matched.group(1):
        return []
    return [part.strip() for part in matched.group(1).split("、") if part.strip()]


def period_of(evidence) -> str | None:
    matched = re.search(r"期次：(期次-[^；，。\s]+)", evidence or "")
    return matched.group(1) if matched else None


def pkey(period: str):
    matched = re.search(r"(\d+)$", period or "")
    return (int(matched.group(1)) if matched else 10**6, period or "")


def key_problem(value) -> str | None:
    """返回五句不符点之一；合法则返回 None。"""
    parts = unkey(value).split("|")
    if len(parts) != 3 or not all(parts):
        return say("frag.074")
    kind, host = parts[0], parts[1]
    if kind not in SEG_TYPE:
        return say("frag.075")
    if kind in ("画面", "消费者", "事件"):
        bits = host.split(" ")
        if len(bits) != 2 or not all(bits) or "  " in host:
            return say("frag.076")
        return None
    if kind == "接口":
        if re.fullmatch(r"[A-Z]+ /\S*", host) is None:
            return say("frag.077")
        return None
    if kind == "定时":
        if " " in host:
            return say("frag.078")
        return None
    return say("frag.075")


def key_ok(value) -> bool:
    return key_problem(value) is None


def row_phrase(rows: list[int]) -> str:
    ordered = []
    for number in rows:
        if number not in ordered:
            ordered.append(number)
    return "第 " + "、".join(str(number) for number in ordered) + " 行"


def pct_text(ratio: Decimal) -> str:
    percent = (ratio * Decimal(100)).quantize(Decimal("0.01"))
    if percent == percent.to_integral_value():
        return f"{int(percent)}%"
    return f"{percent.normalize()}%"


def qty(evidence: str, user: str):
    """调用量三段。返回 (量, 单位, 错误说明)。"""
    if "调用量：" not in evidence:
        return None, None, "缺 `调用量：`"
    if "期间：研发交付期" not in evidence:
        return None, None, "缺 `期间：研发交付期`"
    segment = evidence.split("调用量：", 1)[1].split("；", 1)[0]
    if re.search(r"\d[,，]\d", segment):
        return None, None, f"量写了千分位（「{segment}」）"
    head = segment.split(" ", 1)[0]
    if head != user:
        return None, None, f"F 编号和本行使用方对不上（「{segment}」）"
    rest = segment[len(user) + 1:]
    if rest[:1] in (" ", "\u3000"):
        return None, None, f"F 编号和量之间多了空格（「{segment}」）"
    token = rest.split(" ", 1)[0]
    if any(ch.isdigit() and ch not in "0123456789" for ch in token):
        return None, None, f"量不是阿拉伯数字（「{segment}」）"
    matched = re.match(r"([0-9]+(?:\.[0-9]+)?)(.*)", rest)
    if not matched:
        return None, None, f"量不是阿拉伯数字（「{segment}」）"
    after = matched.group(2)
    if re.match(r"\S", after[:1]) and after[1:2].isdigit():
        return None, None, f"量里有分组符（「{segment}」）"
    if after[:1].isspace() and after[:1] != " " and after[1:2].isdigit():
        return None, None, f"量里有分组符（「{segment}」）"
    if not after.startswith(" "):
        return None, None, f"量和单位之间缺半角空格（「{segment}」）"
    unit = after[1:]
    if not unit.strip() or unit[0] in (" ", "\u3000"):
        return None, None, f"单位为空或量和单位之间多了空格（「{segment}」）"
    if unit[0].isdigit():
        return None, None, f"量里有分组符（「{segment}」）"
    amount = D(matched.group(1))
    if amount is None:
        return None, None, f"量读不出（「{segment}」）"
    return amount, unit.strip(), None


def cfpq(evidence: str):
    """CFP 消费量。没写返回 (None, None)。"""
    if "CFP 消费量：" not in evidence:
        return None, None
    segment = evidence.split("CFP 消费量：", 1)[1].split("；", 1)[0]
    if re.search(r"\d[,，]\d", segment):
        return None, f"量写了千分位（「{segment}」）"
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", segment):
        return D(segment), None
    matched = re.match(r"[0-9]+(?:\.[0-9]+)?", segment)
    if matched and segment[matched.end():matched.end() + 1] and not segment[matched.end()].isdigit() and segment[matched.end() + 1:matched.end() + 2].isdigit():
        return None, f"量里有分组符（「{segment}」）"
    if any(ch.isdigit() and ch not in "0123456789" for ch in segment):
        return None, f"量不是阿拉伯数字（「{segment}」）"
    return None, f"量不是阿拉伯数字或写了分组符（「{segment}」）"


def query_spans(evidence: str):
    """P1-① 查询结果：从该前缀到其后第一处「；」紧接列前缀，或到格尾。"""
    pattern = r"P1-①：(.*?)(?=；(?:非业务功能理由|专属剥离|白名单|对象清单|P1-[①②]|未另行开发|使用系统|依据|同期证据|独立责任方|变更记录编号|认定依据)：|$)"
    return [matched.group(1) for matched in re.finditer(pattern, evidence or "")]


def along_writes(segment: str):
    """查询结果里每个「沿用」起头的写法。"""
    return list(re.finditer(r"沿用[^；，。：]*?(?:字典|参数)|沿用[^；，。：]*", segment))


def strip_mark(text: str) -> tuple[str, bool]:
    stripped = MARK_TAIL.sub("", text)
    return stripped, stripped != text


def backtick_keys(evidence: str) -> set[str]:
    """反引号里的主键。紧跟在接入、含接入后面的那一个不参与归挂比对。"""
    found = set()
    for matched in re.finditer(r"`([^`]+)`", evidence or ""):
        prefix = evidence[:matched.start()]
        if prefix.endswith("接入：") and not prefix.endswith("他系统接入："):
            continue
        found.add(matched.group(1))
    return found
