# -*- coding: utf-8 -*-
"""重算：下钻状态、份额尾差、池与分摊、恒等式。"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date
from decimal import Decimal

from .load import WorkbookData
from .messages import line, say
from .model import DASH, ENDS, Q2, Options, Sink
from .textutil import (
    D, backtick_keys, callers, cfpq, fset, key_ok, own_l4, period_of, pkey, qty, ref_l4s, rq, strip_mark, tailval, unkey,
)


def run(book: WorkbookData, sink: Sink, opt: Options) -> None:
    _v10(book, sink)
    _v15(book, sink)
    _v19(book, sink)
    _v26(book, sink, opt)
    _v27(book, sink, opt)
    _v29(book, sink, opt)
    _v33(book, sink)
    _v34(book, sink)
    _v35(book, sink, opt)
    _v37(book, sink, opt)
    _v38(book, sink)
    _v39(book, sink)
    _v41(book, sink)


def _functions(book: WorkbookData) -> dict:
    return {rec.get("主键"): rec for rec in book.logical("功能")}


def _machines(book: WorkbookData) -> dict:
    return {unkey(rec.get("主键")): rec for rec in book.logical("机能")}


def _l4_known(book: WorkbookData) -> set[str]:
    return {code.rsplit(".", 1)[0] for code in (rec.get("编码", "") for rec in book.logical("表A")) if "." in code}


def _l4_of(book: WorkbookData, code: str) -> str | None:
    found = []
    for rec in book.logical("表B"):
        if code in fset(rec.get("关联业务功能编号（F-）")):
            owner = own_l4(rec.get("主归属 / 引用", ""))
            if owner:
                found.append(owner)
    return min(found) if found else None


def _chain(book: WorkbookData, rec) -> str:
    functions = _functions(book)
    owner = rec.get("主归属功能编号", "")
    identity = functions[owner].get("功能身份") if owner in functions else DASH
    if identity in ("平台功能", "公共能力"):
        return "不要求"
    if owner == DASH:
        return "缺功能"
    acts = [row for row in book.logical("表B") if owner in fset(row.get("关联业务功能编号（F-）"))]
    if not acts:
        return "缺活动"
    known = _l4_known(book)
    if any(own_l4(row.get("主归属 / 引用", "")) not in known for row in acts):
        return "缺子流程"
    return "完整"


def _groups(book: WorkbookData):
    grouped = defaultdict(list)
    for rec in book.logical("分摊"):
        grouped[(rec.get("期次"), rec.get("池类型"), unkey(rec.get("成本池")))].append(rec)
    return grouped


def _cost_periods(rows, costs: set[str] | None = None) -> dict[str, set[str]]:
    found = defaultdict(set)
    for rec in rows:
        cost = unkey(rec.get("成本池", ""))
        period = rec.get("期次", "")
        if not cost or not period:
            continue
        if costs is not None and cost not in costs:
            continue
        found[cost].add(period)
    return found


def _summary_periods(book: WorkbookData) -> dict[str, str] | None:
    """机能汇总行能唯一归上的分摊期次。归不上时返回 None，调用方改为无法校验。"""
    machines = _machines(book)
    functions = _functions(book)
    by_cost = _cost_periods(book.logical("分摊"))
    by_owner = defaultdict(set)
    for key, machine in machines.items():
        by_owner[machine.get("主归属功能编号", "")].update(by_cost.get(key, set()))
    for code, periods in list(by_owner.items()):
        periods.update(by_cost.get(code, set()))
    users = defaultdict(set)
    for rec in book.logical("分摊"):
        user = rec.get("使用方业务功能", "")
        period = rec.get("期次", "")
        if user and period:
            users[user].add(period)
    assigned = {}
    for rec in book.logical("汇总"):
        key = unkey(rec.get("主键"))
        machine = machines.get(key)
        owner = machine.get("主归属功能编号") if machine else ""
        if owner not in functions or functions[owner].get("功能身份") != "业务功能":
            continue
        own = by_cost.get(key, set())
        if len(own) == 1:
            assigned[key] = next(iter(own))
            continue
        if len(own) > 1:
            return None
        sibling = by_owner.get(owner, set())
        if len(sibling) == 1:
            assigned[key] = next(iter(sibling))
            continue
        if len(sibling) > 1:
            return None
        owned_users = users.get(owner, set())
        if len(owned_users) == 1:
            assigned[key] = next(iter(owned_users))
            continue
        return None
    return assigned


def _base_for(book: WorkbookData, period: str, assigned: dict[str, str] | None) -> dict[str, Decimal] | None:
    if assigned is None:
        return None
    functions = _functions(book)
    machines = _machines(book)
    base = defaultdict(Decimal)
    for rec in book.logical("汇总"):
        key = unkey(rec.get("主键"))
        if assigned.get(key) != period:
            continue
        machine = machines.get(key)
        owner = machine.get("主归属功能编号") if machine else DASH
        if owner in functions and functions[owner].get("功能身份") == "业务功能":
            base[owner] += D(rec.get("列一 不复用")) or Decimal(0)
    return base


def _v10(book: WorkbookData, sink: Sink) -> None:
    if not book.readable(sink, "V-10", '表B'):
        return
    functions = _functions(book)
    for rec in book.logical("表B"):
        codes = fset(rec.get("关联业务功能编号（F-）"))
        if rec.get("执行方式") == "线下" and not codes:
            if rec.get("下钻状态") != "不适用":
                sink.add_fail("V-10", line("V-10", say("l3_recalc.V-10.2", p0=rec.row, p1=rec.get('下钻状态'))))
        elif not codes or book.readable(sink, "V-10", "功能"):
            want = "已下钻" if codes and all(code in functions and functions[code].get("下钻状态") == "已下钻" for code in codes) else "待下钻"
            if rec.get("下钻状态") != want:
                sink.add_fail("V-10", line("V-10", say("l3_recalc.V-10.3", p0=rec.row, p1=want, p2=rec.get('下钻状态'))))
        if rec.get("执行方式") == "线下" and codes:
            sink.add_warn("V-10", line("V-10", say("l3_recalc.V-10.1", p0=rec.row)))


def _v15(book: WorkbookData, sink: Sink) -> None:
    if not book.readable(sink, "V-15", '功能', '机能'):
        return
    rows = book.logical("功能")
    if not rows:
        sink.set_na("V-15", "功能登记表的行")
        return
    for rec in rows:
        want = "已下钻" if any(item.get("主归属功能编号") == rec.get("主键") for item in book.logical("机能")) else "待下钻"
        if rec.get("下钻状态") != want:
            sink.add_fail("V-15", line("V-15", say("l3_recalc.V-15.1", p0=rec.row, p1=want, p2=rec.get('下钻状态'))))


def _want_status(book: WorkbookData, rec) -> str:
    chain = _chain(book, rec)
    kind = rec.get("类型", "")
    evidence = rec.get("来源证据", "")
    if chain in ("完整", "不要求"):
        return "已下钻"
    if kind in ("消息消费者", "事件消费", "定时任务"):
        return "本质无单一归属"
    if kind == "画面":
        return "待下钻"
    if kind == "接口":
        if "待查：" in evidence:
            return "未登记"
        if "被调方功能：" in evidence or "用户" in rec.get("触发方式", "") or "调用方：片外" in evidence:
            return "待下钻"
        caller_ids = callers(evidence)
        if caller_ids:
            machines = _machines(book)
            states = [machines[item].get("下钻状态") if item in machines else "" for item in caller_ids]
            if all(item == "本质无单一归属" for item in states):
                return "本质无单一归属"
            if all(item == "已下钻" for item in states):
                return "已下钻"
            return "待下钻"
        return "未登记"
    return "未登记"


def _v19(book: WorkbookData, sink: Sink) -> None:
    if not book.readable(sink, "V-19", '机能', '功能', '表B', '表A'):
        # 来源标签只依赖本行，其他表阻断不妨碍确认这一项。
        for rec in book.logical("机能"):
            if rec.get("下钻状态") == "未登记" and "待查：" not in rec.get("来源证据", ""):
                sink.add_fail("V-19", line("V-19", say("l3_recalc.V-19.1", p0=rec.row)))
        return
    for rec in book.logical("机能"):
        want = _want_status(book, rec)
        extra = ""
        chain = _chain(book, rec)
        if rec.get("类型") == "接口" and chain not in ("完整", "不要求") and rec.get("下钻状态") == "本质无单一归属" and want != "本质无单一归属":
            extra = say("frag.044")
        if rec.get("下钻状态") != want or (rec.get("下钻状态") == "未登记" and "待查：" not in rec.get("来源证据", "")):
            if rec.get("下钻状态") == "未登记" and "待查：" not in rec.get("来源证据", "") and rec.get("下钻状态") == want:
                sink.add_fail("V-19", line("V-19", say("l3_recalc.V-19.1", p0=rec.row)))
            else:
                sink.add_fail("V-19", line("V-19", say("l3_recalc.V-19.2", p0=rec.row, p1=want, p2=rec.get('下钻状态'), p3=extra)))


def _v26(book: WorkbookData, sink: Sink, opt: Options) -> None:
    names = ("功能点计算表·机能规模汇总", "功能点计算表·数据移动明细", "机能登记表")
    blocked = [name for name in names if name not in book.tables or book.tables[name].blocked]
    if blocked:
        sink.set_unable("V-26", line("V-26", say("check.blocked", p0="、".join(blocked))))
        return
    for logical in ("汇总", "机能"):
        keys = [unkey(rec.get("主键")) for rec in book.logical(logical)]
        if len(keys) != len(set(keys)):
            sink.set_unable("V-26", line("V-26", say("check.ambiguous", p0=book.logical(logical)[0].sheet)))
            return
    summary = {unkey(rec.get("主键")): rec for rec in book.logical("汇总")}
    machines = _machines(book)
    measured = {unkey(rec.get("机能主键")) for rec in book.logical("明细") if rec.get("机能主键") not in ("", DASH)}
    for key in sorted(measured - summary.keys()):
        sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.missing_summary", p0=key)))
    for key, rec in summary.items():
        if key not in machines:
            sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.missing_machine", p0=rec.row, p1=key)))
        elif rec.get("下钻状态") != machines[key].get("下钻状态"):
            sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.state", p0=rec.row, p1=rec.get("下钻状态"), p2=machines[key].get("下钻状态"))))
    if not summary:
        sink.set_na("V-26", "机能规模汇总的行")
        return
    own = defaultdict(Decimal)
    for rec in book.logical("明细"):
        if rec.get("机能主键") != DASH:
            own[unkey(rec.get("机能主键"))] += D(rec.get("列 A 原始规模（不拆分）")) or Decimal(0)
    groups = sorted({rec.get("共享加载画面标识") for rec in book.logical("明细") if rec.get("共享加载画面标识") != DASH})
    expected_b = {key: own.get(key, Decimal(0)) for key in summary}
    inside = set()
    expected_n = {}
    tails = {}
    for shared in groups:
        pool = sum((D(rec.get("列 A 原始规模（不拆分）")) or Decimal(0)) for rec in book.logical("明细") if rec.get("共享加载画面标识") == shared)
        processes = {rec.get("功能过程名") for rec in book.logical("明细") if rec.get("共享加载画面标识") == shared}
        parts = sorted(
            key for key in (unkey(rec.get("主键")) for rec in book.logical("机能"))
            if key.startswith("画面|") and key.split("|")[1].split(" ")[0] == shared
        )
        inside |= set(parts)
        outputs = [
            rec for rec in book.logical("明细")
            if unkey(rec.get("机能主键")) in parts and rec.get("数据移动类型") == "X" and rec.get("功能过程名") in processes
            and rec.get("归属层级") == "区块级" and "只服务：" in rec.get("来源证据", "")
        ]
        counts = {}
        for key in parts:
            objects = set()
            for rec in outputs:
                if unkey(rec.get("机能主键")) != key:
                    continue
                obj = rec.get("数据对象")
                evidence = rec.get("来源证据", "")
                others = [item for item in outputs if item.get("数据对象") == obj and unkey(item.get("机能主键")) != key and "重复输出依据：" not in item.get("来源证据", "")]
                if "重复输出依据：" in evidence or "主显示区块" in evidence:
                    objects.add(obj)
                elif not others:
                    objects.add(obj)
                elif not any("主显示区块" in item.get("来源证据", "") for item in others):
                    sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.6", p0=key, p1=obj)))
            counts[key] = len(objects)
        expected_n.update(counts)
        total_n = sum(counts.values())
        if total_n == 0:
            sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.1", p0=shared, p1=shared)))
            continue
        shares = {key: rq(pool * Decimal(counts[key]) / Decimal(total_n), opt.scale_q) for key in parts}
        diff = pool - sum(shares.values())
        if diff != 0:
            best = max(counts.values())
            target = sorted(key for key in parts if counts[key] == best)[0]
            shares[target] += diff
            tails[target] = diff
        for key in parts:
            expected_b[key] = expected_b.get(key, Decimal(0)) + shares[key]
        total_a = pool + sum(own.get(key, Decimal(0)) for key in parts)
        total_b = sum((D(summary[key].get("列 B 分摊后规模（归集用）")) or Decimal(0)) for key in parts if key in summary)
        if total_a != total_b:
            sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.2", p0=shared, p1=shared, p2=(total_a - total_b))))
    for key, rec in summary.items():
        actual_b = D(rec.get("列 B 分摊后规模（归集用）"))
        if actual_b != expected_b.get(key, Decimal(0)):
            sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.3", p0=key, p1=(actual_b - expected_b.get(key, Decimal(0)) if actual_b is not None else '读不出'))))
        want_n = str(expected_n[key]) if key in inside else DASH
        if rec.get("已落数据对象数") != want_n:
            sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.4", p0=key, p1=want_n, p2=rec.get('已落数据对象数'))))
        written = tailval(rec.get("来源证据", ""))
        if key in tails and written != tails[key]:
            sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.5", p0=key)))
        if key not in tails and written is not None:
            sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.5", p0=key)))
    for key, value in own.items():
        if key in inside or key not in summary:
            continue
        actual = D(summary[key].get("列 B 分摊后规模（归集用）"))
        if actual != value:
            sink.add_fail("V-26", line("V-26", say("l3_recalc.V-26.3", p0=key, p1=(actual - value if actual is not None else '读不出'))))


def _real_token(value: str) -> bool:
    text = unkey(value).strip()
    return text not in ("", DASH)


def _reuse_declaration(declared: str):
    """声明中的类型、机能、版本、契约必须唯一且有实值。"""
    values = {}
    for part in declared.split("；"):
        label, sep, value = part.partition("：")
        if sep and label in ("复用类型", "被复用机能", "版本", "契约引用"):
            if label in values or not _real_token(value):
                return None
            values[label] = unkey(value)
    if set(values) != {"复用类型", "被复用机能", "版本", "契约引用"} or values["复用类型"] not in ("多端", "跨版本"):
        return None
    return values


def _reuse_coefficient(evidence: str):
    """只解释给定系数，不选择组织取值。支持十进制、百分数和分数。"""
    if evidence.count("复用系数：") != 1:
        return None, ""
    raw = evidence.split("复用系数：", 1)[1].split("；", 1)[0].strip()
    match = re.fullmatch(r"(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?%?)(.*)", raw)
    if not match:
        return None, ""
    token, source = match.groups()
    # 系数与出处必须有分界，避免把 0.5abc 等混合值截成 0.5。
    if source and not source.startswith((" ", "（", "(", "，", ",", "；")):
        return None, ""
    try:
        numerator, slash, denominator = token.rstrip("%").partition("/")
        value = Decimal(numerator) / (Decimal(denominator) if slash else 1)
        if token.endswith("%"):
            value /= 100
    except ArithmeticError:
        return None, ""
    if not value.is_finite() or not 0 <= value <= 1:
        return None, ""
    source = source.strip(" （），(),")
    return value, source if _real_token(source) else ""


def _v27(book: WorkbookData, sink: Sink, opt: Options) -> None:
    rows = book.logical("汇总")
    table = book.tables.get("功能点计算表·机能规模汇总")
    if table is None or table.blocked:
        sink.set_unable("V-27", line("V-27", say("check.blocked", p0="功能点计算表·机能规模汇总")))
        return
    if not rows:
        sink.set_na("V-27", "机能规模汇总的行")
        return
    machines = _machines(book)
    ledger = {(unkey(rec.get("主键")), rec.get("建设版本")) for rec in book.logical("登记簿")}
    for rec in rows:
        key = unkey(rec.get("主键"))
        numbers = [D(rec.get(column)) for column in ("列一 不复用", "列二 复用", "列 B 分摊后规模（归集用）")]
        column_1, column_2, column_b = [value if value is not None and value.is_finite() else None for value in numbers]
        reasons = []
        if column_1 != column_b:
            reasons.append(say("frag.045"))
        if column_1 is not None and column_2 is not None and column_2 > column_1:
            reasons.append(say("frag.046"))
        discount = column_1 is not None and column_2 is not None and column_2 < column_1
        declaration = _reuse_declaration(rec.get("复用声明", ""))
        if discount:
            if declaration is None:
                reasons.append(say("frag.047"))
            else:
                reused = declaration["被复用机能"]
                dep = "能力登记簿" if declaration["复用类型"] == "跨版本" else "机能登记表"
                dep_table = book.tables.get(dep)
                if dep_table is None or dep_table.blocked:
                    sink.set_unable("V-27", line("V-27", say("check.blocked", p0=dep)))
                elif declaration["复用类型"] == "跨版本":
                    matching = [item for item in book.logical("登记簿") if unkey(item.get("主键")) == reused and item.get("建设版本") == declaration["版本"]]
                    if len(matching) > 1:
                        sink.set_unable("V-27", line("V-27", say("check.ambiguous", p0=dep)))
                    elif (reused, declaration["版本"]) not in ledger:
                        reasons.append(say("l3_recalc.V-27.version"))
                else:
                    relevant = [unkey(item.get("主键")) for item in book.logical("机能") if unkey(item.get("主键")) in (key, reused)]
                    if len(relevant) != len(set(relevant)):
                        sink.set_unable("V-27", line("V-27", say("check.ambiguous", p0=dep)))
                    else:
                        mine, other = machines.get(key), machines.get(reused)
                        if not (mine and other and mine.get("主归属功能编号") == other.get("主归属功能编号") and mine.get("主归属功能编号") not in ("", DASH)):
                            reasons.append(say("frag.047"))
                        if not (mine and other and mine.get("类型") == other.get("类型") == "画面" and mine.get("端") in ENDS and other.get("端") in ENDS and mine.get("端") != other.get("端")):
                            reasons.append(say("l3_recalc.V-27.end"))
            evidence = rec.get("来源证据", "")
            coefficient, source = _reuse_coefficient(evidence)
            if "复用系数：" not in evidence:
                reasons.append(say("frag.048"))
            elif coefficient is None:
                reasons.append(say("l3_recalc.V-27.coefficient"))
            elif not source:
                reasons.append(say("l3_recalc.V-27.source"))
            if coefficient is not None:
                expected = rq(column_1 * coefficient, opt.scale_q)
                if column_2 != expected:
                    reasons.append(say("l3_recalc.V-27.amount", p0=column_1, p1=coefficient, p2=expected, p3=column_2))
        if reasons:
            sink.add_fail("V-27", line("V-27", say("l3_recalc.V-27.1", p0=key, p1='／'.join(reasons))))


def _v29(book: WorkbookData, sink: Sink, opt: Options) -> None:
    table = book.tables.get("机能登记表")
    if table is None or table.blocked:
        sink.set_unable("V-29", line("V-29", say("check.blocked", p0="机能登记表")))
        return
    rows = book.logical("机能")
    unread = [rec for rec in rows if rec.get("下钻状态") == "未登记"]
    pending = [rec for rec in rows if rec.get("下钻状态") == "待下钻"]
    if opt.state == "正常态" and unread:
        numbers = "、".join(str(rec.row) for rec in unread)
        sink.add_fail("V-29", line("V-29", say("l3_recalc.V-29.1", p0=len(unread), p1=numbers)))
    for rec in rows:
        evidence = rec.get("来源证据", "")
        if "下线建议：" not in evidence:
            continue
        matched = re.search(r"下线建议：([^；]+)；(\d{4}-\d{2}-\d{2})；(\d{4}-\d{2}-\d{2})(?=；|$)", evidence)
        try:
            if matched is None or not _real_token(matched.group(1)) or evidence.count("下线建议：") != 1:
                raise ValueError
            proposed, deadline = date.fromisoformat(matched.group(2)), date.fromisoformat(matched.group(3))
            if proposed > deadline:
                raise ValueError
        except ValueError:
            sink.add_fail("V-29", line("V-29", say("l3_recalc.V-29.invalid", p0=rec.row)))
            continue
        if opt.validation_date is None:
            sink.set_unable("V-29", line("V-29", say("l3_recalc.V-29.2", p0=rec.row)))
        elif opt.validation_date > deadline:
            sink.add_fail("V-29", line("V-29", say("l3_recalc.V-29.expired", p0=rec.row, p1=deadline, p2=opt.validation_date)))
        else:
            sink.add_warn("V-29", line("V-29", say("l3_recalc.V-29.scheduled", p0=rec.row, p1=unkey(rec.get("主键")), p2=deadline, p3=opt.validation_date)))
    if opt.state == "正常态" and opt.closing and pending:
        numbers = "、".join(str(rec.row) for rec in pending)
        sink.add_fail("V-29", line("V-29", say("l3_recalc.V-29.3", p0=len(pending), p1=numbers)))
    elif pending:
        for rec in pending:
            sink.add_warn("V-29", line("V-29", say("l3_recalc.V-29.pending", p0=rec.row, p1=unkey(rec.get("主键")))))


SPLIT = re.compile(r"切分：已指名\s*([\d.]+)\s*／\s*未指名\s*([\d.]+)")


def _split_reasons(rows, period, pool, cost, amount, book: WorkbookData) -> list[str]:
    if pool != "共享池":
        return []
    marked = [rec for rec in rows if "切分：" in rec.get("受益方留痕", "")]
    if not marked:
        return []
    reasons = []
    if len(marked) != len(rows):
        reasons.append(say("frag.049"))
    parsed = []
    for rec in marked:
        matched = SPLIT.search(rec.get("受益方留痕", ""))
        if not matched:
            reasons.append(say("frag.049"))
            continue
        named, unnamed = D(matched.group(1)), D(matched.group(2))
        parsed.append((named, unnamed))
    if any(named is None or unnamed is None or named + unnamed != 1 for named, unnamed in parsed):
        reasons.append(say("frag.049"))
    if len({pair for pair in parsed}) > 1:
        reasons.append(say("frag.049"))
    other = [
        item for item in book.logical("分摊")
        if item.get("池类型") == "未下钻池" and item.get("期次") == period and unkey(item.get("成本池")) == cost
    ]
    other_amounts = {D(item.get("池发生额")) for item in other}
    other_amount = next(iter(other_amounts)) if len(other_amounts) == 1 else None
    for named, unnamed in parsed:
        if named in (None, 0) or unnamed in (None, 0) or other_amount is None or amount is None:
            reasons.append(say("frag.049"))
            continue
        if amount * unnamed != other_amount * named:
            reasons.append(say("frag.049"))
    return reasons


def _v33(book: WorkbookData, sink: Sink) -> None:
    book.readable(sink, "V-33", '分摊')
    groups = _groups(book)
    if not groups:
        sink.set_na("V-33", "需要重算的池")
        return
    alloc_complete = book.readable(sink, "V-33", "分摊")
    scale_readable = book.readable(sink, "V-33", "汇总", "机能", "功能")
    assigned = _summary_periods(book) if alloc_complete and scale_readable else None
    marked = defaultdict(set)
    pool_names = set()
    bare_names = set()
    for rec in book.logical("机能"):
        for matched in re.finditer(r"归挂：([^；]*)", rec.get("来源证据", "")):
            raw = matched.group(1).strip()
            stripped, had = strip_mark(raw)
            if had:
                if raw != stripped and stripped.endswith("）"):
                    sink.add_fail("V-33", line("V-33", say("l3_recalc.V-33.3", p0=rec.get('主键'))))
                pool_names.add(stripped)
                marked[stripped].add(unkey(rec.get("主键")))
            elif raw:
                bare_names.add(raw)
    for (period, pool, cost), rows in groups.items():
        label = f"{period}{pool}{cost}"
        reasons = []
        if str(cost).startswith("归挂：") and book.readable(sink, "V-33", "机能"):
            name = str(cost)[len("归挂："):]
            if name.endswith("）"):
                reasons.append(say("frag.050"))
            elif name in bare_names and name not in pool_names:
                reasons.append(say("frag.050"))
            elif name not in pool_names:
                reasons.append(say("frag.050"))
            else:
                wanted = marked[name]
                for rec in rows:
                    got = backtick_keys(rec.get("来源证据", ""))
                    if got != wanted:
                        reasons.append(say("frag.050"))
                        break
        amounts = {D(rec.get("池发生额")) for rec in rows}
        if len(amounts) > 1:
            reasons.append(say("frag.051"))
            sink.add_fail("V-33", line("V-33", say("l3_recalc.V-33.1", p0=label, p1='／'.join(dict.fromkeys(reasons)))))
            continue
        amount = next(iter(amounts))
        if amount is None:
            reasons.append(say("frag.051"))
            sink.add_fail("V-33", line("V-33", say("l3_recalc.V-33.1", p0=label, p1='／'.join(dict.fromkeys(reasons)))))
            continue
        diff = amount - sum((D(rec.get("分摊额")) or Decimal(0)) for rec in rows)
        if alloc_complete and diff != 0:
            reasons.append(say("frag.052", p0=diff))
        driver = rows[0].get("动因")
        users = [rec.get("使用方业务功能") for rec in rows]
        base = {}
        note = ""
        partial = False
        if driver == "CFP 消费占比":
            errors = []
            for rec in rows:
                quantity, error = cfpq(rec.get("来源证据", ""))
                if error:
                    errors.append(error)
                elif quantity is None:
                    errors.append("缺")
                else:
                    base[rec.get("使用方业务功能")] = quantity
            if any(quantity is None and cfpq(rec.get("来源证据", ""))[0] is None for rec in rows):
                note = say("frag.053")
            if errors or len(base) != len(rows):
                reasons.append(say("frag.054"))
                sink.add_fail("V-33", line("V-33", say("l3_recalc.V-33.2", p0=label, p1='／'.join(dict.fromkeys(reasons)), p2=note)))
                continue
            total = sum(base.values())
        elif driver == "调用量占比":
            units = set()
            errors = []
            for rec in rows:
                quantity, unit, error = qty(rec.get("来源证据", ""), rec.get("使用方业务功能"))
                if error:
                    errors.append(error)
                else:
                    base[rec.get("使用方业务功能")] = quantity
                    units.add(unit)
            if len(units) > 1 or errors or len(base) != len(rows):
                reasons.append(say("frag.055"))
                sink.add_fail("V-33", line("V-33", say("l3_recalc.V-33.1", p0=label, p1='／'.join(dict.fromkeys(reasons)))))
                continue
            total = sum(base.values())
        elif driver == "全盘业务 CFP 占比":
            whole = _base_for(book, period, assigned)
            if whole is None:
                if alloc_complete:
                    reasons.extend(_split_reasons(rows, period, pool, cost, amount, book))
                if reasons:
                    sink.add_fail("V-33", line("V-33", say("l3_recalc.V-33.1", p0=label, p1='／'.join(dict.fromkeys(reasons)))))
                sink.set_unable("V-33", line("V-33", say("l3_recalc.V-33.4", p0=label)))
                continue
            positive = {code: value for code, value in whole.items() if value > 0}
            total = sum(positive.values(), Decimal(0))
            base = {code: positive.get(code, Decimal(0)) for code in users}
            partial = set(users) != set(positive)
        else:
            base = {code: Decimal(1) for code in users}
            total = sum(base.values(), Decimal(0))
            partial = False
        if not alloc_complete:
            if reasons:
                sink.add_fail("V-33", line("V-33", say("l3_recalc.V-33.1", p0=label, p1="／".join(dict.fromkeys(reasons)))))
            continue
        if not total:
            reasons.append(say("frag.056"))
            sink.add_fail("V-33", line("V-33", say("l3_recalc.V-33.1", p0=label, p1='／'.join(dict.fromkeys(reasons)))))
            continue
        shares = {code: rq(amount * base[code] / total, Q2) for code in users}
        remainder = amount - sum(shares.values(), Decimal(0))
        target = None
        if not partial and remainder != 0:
            best = max(shares.values())
            target = sorted(code for code in users if shares[code] == best)[0]
            shares[target] += remainder
        elif partial:
            remainder = None
        for rec in rows:
            code = rec.get("使用方业务功能")
            actual = D(rec.get("分摊额"))
            if actual != shares[code]:
                reasons.append(say("frag.057", p0=(rec.row), p1=(shares[code]), p2=(rec.get('分摊额'))))
            written = tailval(rec.get("来源证据", ""))
            if target is not None and code == target and written != remainder:
                reasons.append(say("frag.058"))
            if (target is None or code != target) and written is not None and not partial:
                reasons.append(say("frag.058"))
        reasons.extend(_split_reasons(rows, period, pool, cost, amount, book))
        if reasons:
            sink.add_fail("V-33", line("V-33", say("l3_recalc.V-33.2", p0=label, p1='／'.join(dict.fromkeys(reasons)), p2=note)))


def _row_tuple(rec) -> tuple:
    columns = ["期次", "池类型", "成本池", "池发生额", "使用方业务功能", "使用方来源档", "动因", "分摊额", "需求编号（标签）", "下钻状态", "来源证据", "受益方留痕"]
    return tuple(unkey(rec.get(column, "")) if column == "成本池" else rec.get(column, "") for column in columns)


def _v34(book: WorkbookData, sink: Sink) -> None:
    book.readable(sink, "V-34", '分摊', '副本')
    if not book.readable(sink, "V-34", "副本"):
        return
    if book.copy_rows is None:
        sink.set_unable("V-34", line("V-34", say("l3_recalc.V-34.1")))
        return
    closed_periods = {rec.get("期次") for rec in book.copy_rows}
    if not closed_periods:
        sink.set_na("V-34", "已结期次的行")
        return
    current = [rec for rec in book.logical("分摊") if rec.get("期次") in closed_periods]
    copies = [rec for rec in book.copy_rows if rec.get("期次") in closed_periods]
    copy_set = {_row_tuple(rec) for rec in copies}
    current_set = {_row_tuple(rec) for rec in current}
    for rec in current:
        if _row_tuple(rec) not in copy_set:
            sink.add_fail("V-34", line("V-34", say("l3_recalc.V-34.2", p0=rec.get('期次'), p1=rec.row)))
    for rec in copies:
        if book.readable(sink, "V-34", "分摊") and _row_tuple(rec) not in current_set:
            sink.add_fail("V-34", line("V-34", say("l3_recalc.V-34.2", p0=rec.get('期次'), p1=rec.row)))


def _v35(book: WorkbookData, sink: Sink, opt: Options) -> None:
    if not book.readable(sink, "V-35", '汇总', '机能', '功能'):
        return
    rows = book.logical("汇总")
    if not rows:
        sink.set_na("V-35", "机能规模汇总的行")
        return
    functions = _functions(book)
    machines = _machines(book)

    def identity(rec):
        machine = machines.get(unkey(rec.get("主键")))
        owner = machine.get("主归属功能编号") if machine else DASH
        return functions[owner].get("功能身份") if owner in functions else DASH

    platform = sum((D(rec.get("列一 不复用")) or Decimal(0)) for rec in rows if identity(rec) in ("平台功能", "公共能力"))
    total = sum((D(rec.get("列一 不复用")) or Decimal(0)) for rec in rows)
    if not total:
        sink.set_na("V-35", "列一之和不为零的机能")
        return
    ratio = platform / total
    if ratio < opt.warn:
        return
    text = say("frag.059") if ratio < opt.limit else say("frag.060")
    shown = (ratio * Decimal(100)).quantize(Decimal("0.1"))
    sink.add_warn("V-35", line("V-35", say("l3_recalc.V-35.1", p0=shown, p1=text)))


def _v37(book: WorkbookData, sink: Sink, opt: Options) -> None:
    book.readable(sink, "V-37", '机能', '分摊')
    unread = [rec for rec in book.logical("机能") if rec.get("下钻状态") == "未登记"]
    alloc = [rec for rec in book.logical("分摊") if rec.get("下钻状态") == "未登记"]
    if not unread and not alloc:
        return
    bits = []
    if unread:
        bits.append(say("frag.061", p0=("、".join(str(rec.row) for rec in unread))))
    if alloc:
        bits.append(say("frag.062", p0=("、".join(str(rec.row) for rec in alloc))))
    count = len(unread) + len(alloc)
    where = "；".join(bits)
    if opt.closing:
        sink.add_fail("V-37", line("V-37", say("l3_recalc.V-37.1", p0=count, p1=where)))
    else:
        sink.add_warn("V-37", line("V-37", say("l3_recalc.V-37.2", p0=count)))


def _v38(book: WorkbookData, sink: Sink) -> None:
    book.readable(sink, "V-38", '分摊', '不计入', '恒等式', '全系统')
    alloc = book.logical("分摊")
    excluded = book.logical("不计入")
    identity = book.logical("恒等式")
    system = book.logical("全系统")
    periods = {rec.get("期次") for rec in alloc} | {period_of(rec.get("来源证据", "")) for rec in excluded if period_of(rec.get("来源证据", ""))}
    if not periods and not identity and not system:
        sink.set_na("V-38", "分摊或不计入投入的期次")
        return
    alloc_complete = book.readable(sink, "V-38", "分摊")
    identity_complete = book.readable(sink, "V-38", "恒等式")
    excluded_complete = book.readable(sink, "V-38", "不计入")
    reasons_by_key = defaultdict(list)

    def add(key, text, *, move_row=False, scope_system=False):
        reasons_by_key[key].append((text, move_row, scope_system))

    for rec in alloc:
        if not book.readable(sink, "V-38", "表B"):
            break
        expect = _l4_of(book, rec.get("使用方业务功能", ""))
        if expect != rec.case:
            add(rec.get("期次"), say("frag.063", p0=(rec.row)), move_row=True)
    present = {(rec.case, rec.get("期次")) for rec in alloc}
    counted = defaultdict(int)
    for rec in identity:
        period, scope = rec.get("期次"), rec.get("范围")
        if scope == "本片合计":
            add(period, say("frag.064"), scope_system=True)
            continue
        if scope != rec.case:
            add(period, say("frag.065"), scope_system=True)
        counted[(scope, period)] += 1
        if D(rec.get("Σ剔除额")) != Decimal("0.00") and D(rec.get("Σ剔除额")) != Decimal("0"):
            add(period, say("frag.067", p0=(rec.get('Σ剔除额'))))
        if D(rec.get("实际成本总额")) != (D(rec.get("Σ分摊额")) or Decimal(0)) + (D(rec.get("Σ剔除额")) or Decimal(0)):
            add(period, say("frag.068", p0=(rec.get('实际成本总额'))))
        alloc_table = book.tables.get("分摊表·" + scope)
        scope_readable = alloc_table is not None and not alloc_table.blocked
        if not scope_readable:
            # 无分表仍是缺失；已有但阻断的分表不能当作零。
            if alloc_table is not None and alloc_table.blocked:
                continue
        if (scope, period) not in present:
            add(period, say("frag.064"), scope_system=True)
            continue
        total_alloc = sum((D(item.get("分摊额")) or Decimal(0)) for item in alloc if item.get("期次") == period and item.case == scope)
        if D(rec.get("Σ分摊额")) != total_alloc:
            add(period, say("frag.066", p0=(D(rec.get('Σ分摊额')) - total_alloc if D(rec.get('Σ分摊额')) is not None else '读不出')))
    for scope, period in present:
        if identity_complete and counted[(scope, period)] == 0:
            add(period, say("frag.064"), scope_system=True)
    all_periods = {rec.get("期次") for rec in alloc} | {period_of(rec.get("来源证据", "")) for rec in excluded if period_of(rec.get("来源证据", ""))}
    for rec in system:
        if alloc_complete and excluded_complete and rec.get("期次") not in all_periods:
            add(rec.get("期次"), say("frag.064"), scope_system=True)
    for period in sorted(periods, key=pkey):
        if not book.readable(sink, "V-38", "全系统"):
            break
        rows = [rec for rec in system if rec.get("期次") == period and rec.get("范围") == "本片合计"]
        if any(rec.get("范围") != "本片合计" for rec in system if rec.get("期次") == period):
            add(period, say("frag.064"), scope_system=True)
        if len(rows) != 1:
            add(period, say("frag.064"), scope_system=True)
            continue
        rec = rows[0]
        total_alloc = sum((D(item.get("分摊额")) or Decimal(0)) for item in alloc if item.get("期次") == period)
        removed = [item for item in excluded if period_of(item.get("来源证据", "")) == period]
        removed_sum = sum((D(item.get("投入量")) or Decimal(0)) for item in removed)
        if alloc_complete and D(rec.get("Σ分摊额")) != total_alloc:
            add(period, say("frag.066", p0=(D(rec.get('Σ分摊额')) - total_alloc if D(rec.get('Σ分摊额')) is not None else '读不出')))
        if excluded_complete and D(rec.get("Σ剔除额")) != removed_sum:
            add(period, say("frag.067", p0=(D(rec.get('Σ剔除额')) - removed_sum if D(rec.get('Σ剔除额')) is not None else '读不出')))
        if D(rec.get("实际成本总额")) != (D(rec.get("Σ分摊额")) or Decimal(0)) + (D(rec.get("Σ剔除额")) or Decimal(0)):
            add(period, say("frag.068", p0=((D(rec.get("实际成本总额")) or Decimal(0)) - ((D(rec.get("Σ分摊额")) or Decimal(0)) + (D(rec.get("Σ剔除额")) or Decimal(0))))))
        subtotal = sum((D(item.get("Σ分摊额")) or Decimal(0)) for item in identity if item.get("期次") == period and item.get("范围") != "本片合计")
        if identity_complete and D(rec.get("Σ分摊额")) != subtotal:
            add(period, say("frag.065"), scope_system=True)
    for period, tagged in reasons_by_key.items():
        unique = []
        move_row = False
        scope_system = False
        for text, row_flag, system_flag in tagged:
            if text not in unique:
                unique.append(text)
            move_row = move_row or row_flag
            scope_system = scope_system or system_flag
        action = say("frag.069") if move_row else say("frag.070")
        scope = "全系统" if scope_system else "分摊表"
        sink.add_fail("V-38", line("V-38", say("l3_recalc.V-38.1", p0=period, p1=scope, p2='／'.join(unique), p3=action)))


def _v39(book: WorkbookData, sink: Sink) -> None:
    book.readable(sink, "V-39", '不计入', '分摊')
    pattern = re.compile(r"折算：\s*([\d.]+)\s*工时\s*×\s*([\d.]+)")
    targets = []
    for rec in book.logical("不计入"):
        targets.append(("不计入投入清单", rec, rec.get("投入量"), period_of(rec.get("来源证据", ""))))
    for rec in book.logical("分摊"):
        targets.append(("分摊表", rec, rec.get("池发生额"), rec.get("期次")))
    if not any("折算：" in rec.get("来源证据", "") or rec.get("对象类别") == "线下工时" or re.search(r"\d+(?:\.\d+)? ?工时", rec.get("来源证据", "")) for _name, rec, _amt, _period in [(item[0], item[1], item[2], item[3]) for item in targets]):
        # 上面的条件写得过绕。没有折算对象就不适用。
        pass
    interesting = [item for item in targets if "折算：" in item[1].get("来源证据", "") or item[1].get("对象类别") == "线下工时" or re.search(r"\d+(?:\.\d+)? ?工时", item[1].get("来源证据", ""))]
    if not interesting:
        sink.set_na("V-39", "工时折算行")
        return
    prices = defaultdict(set)
    for name, rec, amount, period in interesting:
        evidence = rec.get("来源证据", "")
        matched = pattern.search(evidence)
        label = rec.get("主键") or rec.get("成本池")
        hours_written = rec.get("对象类别") == "线下工时" or re.search(r"\d+(?:\.\d+)?\s*工时", evidence)
        if not matched and hours_written:
            sink.add_fail("V-39", line("V-39", say("l3_recalc.V-39.1", p0=name, p1=rec.row)))
        if not matched:
            continue
        hours, price = D(matched.group(1)), D(matched.group(2))
        if hours is None or price is None or D(amount) is None or rq(hours * price, Q2) != D(amount):
            sink.add_fail("V-39", line("V-39", say("l3_recalc.V-39.2", p0=name, p1=rec.row, p2=matched.group(1), p3=matched.group(2), p4=(rq(hours * price, Q2) if hours is not None and price is not None else '读不出'), p5=amount)))
        source = re.search(r"单价出处：([^；]*)", evidence)
        if not source or source.group(1).strip() in ("", DASH):
            sink.add_fail("V-39", line("V-39", say("l3_recalc.V-39.3", p0=name, p1=rec.row)))
        if period and price is not None:
            prices[period].add(price)
    for period, values in prices.items():
        if len(values) > 1:
            shown = " 与 ".join(str(item) for item in sorted(values))
            sink.add_fail("V-39", line("V-39", say("l3_recalc.V-39.4", p0=shown, p1=f"{period}：")))


def _external(book: WorkbookData) -> set[str]:
    names = set()
    for rec in book.logical("表B"):
        for matched in re.finditer(r"外部应用：([^；]+)", rec.get("来源证据", "")):
            names.add(matched.group(1).strip())
    return names


def _systems(book: WorkbookData, codes: list[str]) -> set[str]:
    found = set()
    for rec in book.logical("表B"):
        if set(fset(rec.get("关联业务功能编号（F-）"))) & set(codes):
            found |= set(fset(rec.get("承载系统")))
    return found - _external(book)


def _build_users(book: WorkbookData, costs: set[str]) -> set[str]:
    rows = [rec for rec in list(book.logical("分摊")) + list(book.copy_rows or []) if unkey(rec.get("成本池")) in costs]
    if not rows:
        return set()
    earliest = min((rec.get("期次") for rec in rows), key=pkey)
    return {rec.get("使用方业务功能") for rec in rows if rec.get("期次") == earliest}


def _reused_systems(book: WorkbookData, key: str) -> set[str]:
    machines = _machines(book)
    functions = _functions(book)
    machine = machines.get(key)
    if not machine:
        return set()
    owner = machine.get("主归属功能编号")
    identity = functions[owner].get("功能身份") if owner in functions else None
    if identity == "业务功能":
        return _systems(book, [owner])
    if identity in ("平台功能", "公共能力"):
        return _systems(book, list(_build_users(book, {key, owner})))
    if identity == "数据功能":
        trace = machine.get("受益方留痕", "")
        acts = set(re.findall(r"S-\d+\.\d+\.\d+", trace.split("受益活动：", 1)[1].split("来源档：", 1)[0])) if "受益活动：" in trace else set()
        found = set()
        for rec in book.logical("表B"):
            if rec.get("主键") in acts:
                found |= set(fset(rec.get("承载系统")))
        return found - _external(book)
    return set()


def _v41(book: WorkbookData, sink: Sink) -> None:
    book.readable(sink, "V-41", '分摊', '不计入')
    machines = _machines(book)
    functions = _functions(book)
    seen = False
    for rec in book.logical("分摊"):
        evidence = rec.get("来源证据", "")
        for matched in re.finditer(r"(?<!他系统)(?:含)?接入：", evidence):
            seen = True
            wrapped = re.match(r"`([^`]+)`", evidence[matched.end():])
            if not wrapped or not key_ok(wrapped.group(1)) or (book.readable(sink, "V-41", "机能") and wrapped.group(1) not in machines):
                sink.add_fail("V-41", line("V-41", say("l3_recalc.V-41.2", p0=rec.row)))
                continue
            if not book.readable(sink, "V-41", "机能", "功能", "表B", "分摊", "副本"):
                continue
            key = wrapped.group(1)
            left = _systems(book, [rec.get("使用方业务功能")])
            right = _reused_systems(book, key)
            if not left or not right:
                sink.add_fail("V-41", line("V-41", say("l3_recalc.V-41.3", p0=rec.row)))
                continue
            if not (left & right):
                sink.add_fail("V-41", line("V-41", say("l3_recalc.V-41.3", p0=rec.row)))
    for rec in book.logical("不计入"):
        matched = re.match(r"他系统接入：(.+)", rec.get("不计入原因", ""))
        if not matched:
            continue
        seen = True
        reasons = []
        if rec.get("对象类别") != "进池前剔除":
            reasons.append(say("frag.071"))
        pool = re.search(r"原池：(\S+) (`[^`]+`|[^；]+)", rec.get("来源证据", ""))
        if not pool:
            reasons.append(say("frag.071"))
        elif book.readable(sink, "V-41", "机能", "功能", "表B", "分摊", "副本"):
            kind, cost = pool.group(1), unkey(pool.group(2).strip())
            if key_ok(cost):
                right = _reused_systems(book, cost) if cost in machines else set()
                if cost not in machines:
                    reasons.append(say("frag.072"))
            elif re.fullmatch(r"F-[A-Za-z0-9.\-]+", cost):
                right = _systems(book, list(_build_users(book, {cost})))
            else:
                users = {item.get("使用方业务功能") for item in list(book.logical("分摊")) + list(book.copy_rows or []) if unkey(item.get("成本池")) == cost and item.get("期次") == period_of(rec.get("来源证据", ""))}
                right = _systems(book, list(users))
            if right and right & set(fset(matched.group(1))):
                reasons.append(say("frag.071"))
            if not right and "`他系统接入：` 的行缺 `原池：`" not in "".join(reasons):
                reasons.append(say("frag.073"))
        if reasons:
            sink.add_fail("V-41", line("V-41", say("l3_recalc.V-41.1", p0=rec.row, p1='／'.join(dict.fromkeys(reasons)))))
    if not seen and "V-41" not in sink.fail:
        sink.set_na("V-41", "写了接入或他系统接入的行")
