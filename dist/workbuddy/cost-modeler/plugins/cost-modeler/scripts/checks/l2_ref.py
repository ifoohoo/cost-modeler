# -*- coding: utf-8 -*-
"""跨表引用。缺了方案点名的外部输入时记无法校验，不把缺输入当成通过。"""
from __future__ import annotations

import re
from collections import defaultdict

from .load import WorkbookData
from .messages import line, say
from .model import DASH, EXPORT_FILES, TABLE_A_SHEET, WL, Sink
from .textutil import along_writes, fset, key_ok, own_l4, pkey, query_spans, ref_l4s, unkey


def run(book: WorkbookData, sink: Sink) -> None:
    _v06(book, sink)
    _v07(book, sink)
    _v08(book, sink)
    _v09(book, sink)
    _v11(book, sink)
    _v12(book, sink)
    _v13(book, sink)
    _v20(book, sink)
    _v21(book, sink)
    _v23(book, sink)
    _v25(book, sink)
    _v28(book, sink)
    _v30(book, sink)
    _v36(book, sink)
    _v40(book, sink)


def _v06(book: WorkbookData, sink: Sink) -> None:
    if book.catalog is None or book.catalog_missing_files:
        sink.set_unable("V-06", line(
            "V-06",
            say("l2_ref.V-06.1"),
        ))
        return
    known = {}
    for rec in book.logical("机能"):
        known[unkey(rec.get("主键", ""))] = rec
    for name in sorted(book.catalog - set(known)):
        sink.add_fail("V-06", line("V-06", say("l2_ref.V-06.2", p0=name)))
    for rec in book.logical("机能"):
        if rec.get("来源证据", "").startswith("机器导出：") and unkey(rec.get("主键", "")) not in book.catalog:
            sink.add_fail("V-06", line("V-06", say("l2_ref.V-06.3", p0=rec.row)))


def _v07(book: WorkbookData, sink: Sink) -> None:
    codes = {rec.get("编码", "") for rec in book.logical("表A")}
    for rec in book.logical("表B"):
        if rec.get("主键", "") not in codes:
            sink.add_fail("V-07", line("V-07", say("l2_ref.V-07.1", p0=rec.row, p1=rec.get('主键', ''))))


def _v08(book: WorkbookData, sink: Sink) -> None:
    functions = {rec.get("主键"): rec for rec in book.logical("功能")}
    for rec in book.logical("表B"):
        for code in fset(rec.get("关联业务功能编号（F-）")):
            row = functions.get(code)
            if row is None:
                sink.add_fail("V-08", line("V-08", say("l2_ref.V-08.1", p0=rec.row, p1=code)))
            elif row.get("功能身份") != "业务功能":
                sink.add_fail("V-08", line("V-08", say("l2_ref.V-08.2", p0=rec.row, p1=code)))


def _v09(book: WorkbookData, sink: Sink) -> None:
    known = {code.rsplit(".", 1)[0] for code in (rec.get("编码", "") for rec in book.logical("表A")) if "." in code}
    targets = []
    for rec in book.logical("表B"):
        text = rec.get("主归属 / 引用", "")
        if "引用 L4：" not in text:
            continue
        targets.append(rec)
        owner = own_l4(text)
        refs = ref_l4s(text)
        if owner not in known or any(item not in known or item == owner for item in refs) or not rec.get("主键", "").startswith((owner or "") + "."):
            sink.add_fail("V-09", line("V-09", say("l2_ref.V-09.1", p0=rec.row, p1=('、'.join(refs) or text))))
    if not targets:
        sink.set_na("V-09", "引用 L4 的行")


def _cell_letters(cell: str) -> frozenset[str]:
    """角色格字母按集合算：空与 `—` 都是空集，`AR` 与 `RA` 相同。"""
    text = (cell or "").strip()
    if text in ("", DASH):
        return frozenset()
    return frozenset(ch for ch in text if not ch.isspace())


def _v11(book: WorkbookData, sink: Sink) -> None:
    if book.previous is None:
        sink.set_unable("V-11", line("V-11", say("l2_ref.V-11.1")))
        return
    table = book.tables.get(TABLE_A_SHEET)
    current_roles = table.role_headers if table else []
    previous_roles = [book.previous_headers[col - 1] for col in book.previous_role_cols if 0 < col <= len(book.previous_headers)]
    common = [role for role in current_roles if role in set(previous_roles)]
    # 两版角色列列头集合不同的，对应列整列算变化。
    differ = sorted(set(current_roles) ^ set(previous_roles))
    current = {rec.get("编码"): rec for rec in book.logical("表A")}
    tail = say("frag.027")
    for rec in book.previous:
        code = rec.get("编码", "")
        now = current.get(code)
        if now is None:
            sink.add_warn("V-11", line("V-11", say("l2_ref.V-11.2", p0=code, p1=tail)))
            continue
        segments = []
        if now.get("活动名称") != rec.get("活动名称"):
            segments.append(say("frag.028", p0=(rec.get('活动名称')), p1=(now.get('活动名称'))))
        cells = []
        for role in differ:
            old = rec.get(role) if role in previous_roles else None
            new = now.get(role) if role in current_roles else None
            cells.append((role, "（无此列）" if old is None else (old or ""), "（无此列）" if new is None else (new or "")))
        for role in common:
            old, new = rec.get(role, ""), now.get(role, "")
            if _cell_letters(old) != _cell_letters(new):
                cells.append((role, old, new))
        for role, old, new in cells:
            segments.append(say("frag.079", p0=role, p1=old, p2=new))
        if segments:
            sink.add_warn("V-11", line(
                "V-11",
                say("l2_ref.V-11.3", p0=code, p1='；'.join(segments), p2=tail),
            ))


def _v12(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("补登")
    if not rows:
        sink.set_na("V-12", "流程补登清单的行")
        return
    codes = {rec.get("编码", "") for rec in book.logical("表A")}
    for rec in rows:
        reasons = []
        if rec.get("表 A 检索结果") == "命中且三元组全等" and rec.get("处理结果") != "不许补":
            reasons.append(say("frag.029"))
        matched = re.fullmatch(r"已补入表 A：(\S+)", rec.get("处理结果", ""))
        if matched:
            if rec.get("三问结论") != "过/过/过":
                reasons.append(say("frag.030"))
            if rec.get("拟挂业务功能编号（F-）") == DASH:
                reasons.append(say("frag.031"))
            if matched.group(1) not in codes:
                reasons.append(say("frag.032"))
        if reasons:
            sink.add_fail("V-12", line("V-12", say("l2_ref.V-12.1", p0=rec.row, p1='／'.join(reasons))))


def _cost_periods(rows, costs: set[str]) -> set[str]:
    found = set()
    for item in rows:
        if unkey(item.get("成本池", "")) in costs and item.get("期次"):
            found.add(item.get("期次"))
    return found


def _object_list(evidence: str) -> list[str]:
    matched = re.search(r"对象清单：(.*)", evidence)
    if not matched:
        return []
    items = []
    for part in matched.group(1).split("；"):
        if "：" in part:
            break
        if part.strip():
            items.append(part.strip())
    return items


def _object_mismatch(rec, listed, wanted) -> str:
    extra = "、".join(sorted(set(listed) - wanted)) or "无"
    lack = "、".join(sorted(wanted - set(listed))) or "无"
    return line("V-13", say("l2_ref.V-13.1", p0=rec.row, p1=rec.get('主键'), p2=extra, p3=lack))


def _v13_objects(book: WorkbookData, sink: Sink, rec, listed, wanted, costs: set[str]) -> None:
    if book.copy_rows is None:
        sink.set_unable("V-13", line(
            "V-13",
            say("l2_ref.V-13.2", p0=rec.row, p1=rec.get('主键')),
        ))
        return
    current_periods = _cost_periods(book.logical("分摊"), costs)
    copy_periods = _cost_periods(book.copy_rows, costs)
    all_periods = current_periods | copy_periods
    open_periods = current_periods - copy_periods
    if not all_periods:
        sink.add_warn("V-13", line(
            "V-13",
            say("l2_ref.V-13.5", p0=rec.row, p1=rec.get('主键')),
        ).replace("处理：该行不合格，改正后重跑。", "预警，不拦截。"))
        building = False
    elif len(open_periods) == 1 or (not open_periods and len(current_periods) == 1):
        current = next(iter(open_periods or current_periods))
        building = min(all_periods, key=pkey) == current
    else:
        sink.set_unable("V-13", line(
            "V-13",
            say("l2_ref.V-13.3", p0=rec.row, p1=rec.get('主键')),
        ))
        return
    if len(listed) != len(set(listed)) or (set(listed) != wanted if building else not wanted <= set(listed)):
        sink.add_fail("V-13", _object_mismatch(rec, listed, wanted))


def _v13(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("功能")
    if not rows:
        sink.set_na("V-13", "功能登记表的行")
        return
    machines = book.logical("机能")
    details = book.logical("明细")
    for rec in rows:
        evidence = rec.get("来源证据", "")
        identity = rec.get("功能身份", "")
        if identity in ("平台功能", "公共能力"):
            if rec.get("平台功能用户") == DASH or rec.get("平台白名单类别") not in WL or "非业务功能理由：" not in evidence:
                sink.add_fail("V-13", line("V-13", say("l2_ref.V-13.6", p0=rec.row, p1=rec.get('主键'))))
            missing = [prefix for prefix in ("专属剥离：", "白名单：", "对象清单：") if prefix not in evidence]
            if not re.search(r"P1-[①②]：", evidence):
                missing.append("P1-①：")
            if missing:
                sink.add_fail("V-13", line("V-13", say("l2_ref.V-13.7", p0=rec.row, p1=rec.get('主键'), p2='、'.join(missing))))
            listed = _object_list(evidence)
            owned = {unkey(item.get("主键", "")) for item in machines if item.get("主归属功能编号") == rec.get("主键")}
            costs = owned | {rec.get("主键", "")}
            wanted = {
                item.get("数据对象")
                for item in details
                if item.get("机能主键") != DASH and unkey(item.get("机能主键")) in owned and item.get("数据移动类型") in ("E", "X", "W")
            }
            _v13_objects(book, sink, rec, listed, wanted, costs)
            if re.search(r"沿用通用(字典|参数)", evidence):
                marker = re.search(r"未另行开发：([^；]*)", evidence)
                if not marker or marker.group(1).strip() in ("", DASH):
                    sink.add_fail("V-13", line("V-13", say("l2_ref.V-13.9", p0=rec.row, p1=rec.get('主键'))))
            for span in query_spans(evidence):
                for write in along_writes(span):
                    text = write.group(0)
                    previous = span[:write.start()].rstrip("`")[-1:]
                    if text not in ("沿用通用字典", "沿用通用参数") or previous not in ("", "为", "，", "。", "：", "；"):
                        sink.add_fail("V-13", line("V-13", say("l2_ref.V-13.11", p0=rec.row, p1=rec.get('主键'), p2=text)))
            if rec.get("平台白名单类别", "").split(" ", 1)[0] == "4":
                for span in query_spans(evidence):
                    if not re.search(r"技术性取值|业务取值|沿用", span):
                        sink.add_fail("V-13", line("V-13", say("l2_ref.V-13.12", p0=rec.row, p1=rec.get('主键'))))
                        break
            if "白名单：" in evidence:
                matched = re.search(r"白名单：第 ?([0-9]+) ?类", evidence)
                number = rec.get("平台白名单类别", "").split(" ", 1)[0]
                if not matched or matched.group(1) != number:
                    sink.add_fail("V-13", line("V-13", say("l2_ref.V-13.10", p0=rec.row, p1=rec.get('主键'), p2=number)))
        if identity == "公共能力":
            matched = re.search(r"使用系统：(.*?)；(依据|同期证据)：", evidence)
            names = set()
            if matched:
                names = {item.strip() for item in matched.group(1).split("；") if item.strip()}
            if not matched or len(names) < 2:
                sink.add_fail("V-13", line("V-13", say("l2_ref.V-13.8", p0=rec.row, p1=rec.get('主键'))))
        if identity not in ("平台功能", "公共能力") and (rec.get("平台功能用户") != DASH or rec.get("平台白名单类别") != DASH):
            sink.add_fail("V-13", line("V-13", say("l2_ref.V-13.4", p0=rec.row, p1=rec.get('主键'))))


def _acts(rec) -> tuple[set[str] | None, str | None]:
    matched = re.search(r"受益活动：(.*?)；来源档：(\S+)", rec.get("受益方留痕", ""))
    if not matched:
        return None, None
    return set(fset(matched.group(1))), matched.group(2)


def _v20(book: WorkbookData, sink: Sink) -> None:
    rows = [rec for rec in book.logical("机能") if rec.get("下钻状态") == "本质无单一归属"]
    if not rows:
        sink.set_na("V-20", "「本质无单一归属」的机能行")
        return
    activities = {rec.get("主键") for rec in book.logical("表B")}
    machines = {unkey(rec.get("主键")): rec for rec in book.logical("机能")}
    for rec in rows:
        found, source = _acts(rec)
        reasons = []
        if found is None or any(item not in activities for item in found):
            missing = "、".join(sorted(item for item in (found or []) if item not in activities)) or "（没有受益活动）"
            reasons.append(say("frag.033", p0=missing))
        if source not in ("接口契约", "菜单-功能映射", "事件订阅表", "人工认定"):
            reasons.append(say("frag.034"))
        caller_ids = [item for item in re.findall(r"`([^`]+)`", rec.get("来源证据", "").split("随调用方：", 1)[1])] if "随调用方：" in rec.get("来源证据", "") else []
        if caller_ids and found is not None:
            union = set()
            for caller in caller_ids:
                other = machines.get(caller)
                if other:
                    other_acts, _source = _acts(other)
                    union |= other_acts or set()
            if union != found:
                reasons.append(say("frag.035"))
        if reasons:
            sink.add_fail("V-20", line("V-20", say("l2_ref.V-20.1", p0=rec.row, p1='／'.join(reasons))))


def _v21(book: WorkbookData, sink: Sink) -> None:
    functions = {rec.get("主键") for rec in book.logical("功能")}
    machines = {unkey(rec.get("主键")): rec for rec in book.logical("机能")}
    for rec in book.logical("机能"):
        owner = rec.get("主归属功能编号", "")
        reasons = []
        if rec.get("下钻状态") not in ("待下钻", "未登记") and owner == DASH:
            reasons.append(say("frag.036"))
        if owner != DASH and len(fset(owner)) != 1:
            reasons.append(say("frag.037"))
        elif owner != DASH and owner not in functions:
            reasons.append(say("frag.038"))
        if "随调用方：" in rec.get("来源证据", ""):
            caller_ids = re.findall(r"`([^`]+)`", rec.get("来源证据", "").split("随调用方：", 1)[1])
            owners = sorted(machines[item].get("主归属功能编号") for item in caller_ids if item in machines and machines[item].get("主归属功能编号") != DASH)
            if owners and owner != owners[0]:
                reasons.append(say("frag.039"))
        if "主归属断法：F 编号升序" in rec.get("来源证据", ""):
            triggered = sorted({
                code
                for detail in book.logical("明细")
                if unkey(detail.get("机能主键")) == unkey(rec.get("主键"))
                for code in fset(detail.get("触发业务功能编号"))
            })
            if not triggered or owner != triggered[0]:
                reasons.append(say("frag.040"))
        if reasons:
            sink.add_fail("V-21", line("V-21", say("l2_ref.V-20.1", p0=rec.row, p1='／'.join(reasons))))


def _v23(book: WorkbookData, sink: Sink) -> None:
    hosts = set()
    for rec in book.logical("机能"):
        key = unkey(rec.get("主键", ""))
        if key.startswith("画面|") and "|" in key:
            hosts.add(key.split("|")[1].split(" ")[0])
    for rec in book.logical("明细"):
        shared = rec.get("共享加载画面标识", "")
        if shared != DASH and shared not in hosts:
            sink.add_fail("V-23", line("V-23", say("l2_ref.V-23.1", p0=rec.row, p1=shared)))


def _v25(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("明细")
    if not rows:
        sink.set_na("V-25", "数据移动明细的行")
        return
    functions = {rec.get("主键") for rec in book.logical("功能")}
    for rec in rows:
        for code in fset(rec.get("触发业务功能编号")):
            if code not in functions:
                sink.add_fail("V-25", line("V-25", say("l2_ref.V-25.2", p0=rec.get('功能过程名'), p1=code)))
    groups = defaultdict(lambda: defaultdict(list))
    for rec in rows:
        key = unkey(rec.get("机能主键")) if rec.get("机能主键") != DASH else ""
        if rec.get("共享加载画面标识") != DASH:
            host = rec.get("共享加载画面标识")
        elif key.startswith("画面|"):
            host = key.split("|")[1].split(" ")[0]
        else:
            host = key
        groups[(host, rec.get("功能过程名"))][rec.get("触发业务功能编号")].append(rec)
    for (_host, process), values in groups.items():
        if len(values) <= 1:
            continue
        for value, group in values.items():
            numbers = "、".join(str(rec.row) for rec in group)
            sink.add_fail("V-25", line("V-25", say("l2_ref.V-25.1", p0=process, p1=numbers, p2=value)))


def _v28(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("链路")
    if not rows:
        sink.set_na("V-28", "链路核对视图的行")
        return
    machines = {unkey(rec.get("主键")): rec for rec in book.logical("机能")}
    for rec in rows:
        other = machines.get(unkey(rec.get("主键")))
        if other and other.get("下钻状态") != rec.get("下钻状态"):
            sink.add_fail("V-28", line("V-28", say("l2_ref.V-28.1", p0=unkey(rec.get('主键')), p1=rec.get('下钻状态'), p2=other.get('下钻状态'))))


def _v30(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("分摊")
    if not rows:
        sink.set_na("V-30", "分摊表的行")
        return
    functions = {rec.get("主键"): rec for rec in book.logical("功能")}
    for rec in rows:
        code = rec.get("使用方业务功能", "")
        row = functions.get(code)
        if row is None:
            sink.add_fail("V-30", line("V-30", say("l2_ref.V-30.1", p0=rec.row, p1=code)))
        elif row.get("功能身份") != "业务功能":
            sink.add_fail("V-30", line("V-30", say("l2_ref.V-30.2", p0=rec.row, p1=code)))


def _v36(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("登记簿")
    if not rows:
        sink.set_na("V-36", "能力登记簿的行")
        return
    functions = {rec.get("主键"): rec for rec in book.logical("功能")}
    machines = {unkey(rec.get("主键")): rec for rec in book.logical("机能")}
    for rec in rows:
        machine = machines.get(unkey(rec.get("主键")))
        owner = machine.get("主归属功能编号") if machine else DASH
        reasons = []
        if owner not in functions or functions[owner].get("功能身份") != "业务功能":
            reasons.append(say("frag.041"))
        users = fset(rec.get("建设期使用方"))
        expect = "潜在共通能力" if len(users) == 1 else "共通能力"
        if rec.get("共通标记") != expect:
            reasons.append(say("frag.042") if len(users) == 1 else say("frag.043"))
        if reasons:
            sink.add_fail("V-36", line("V-36", say("l2_ref.V-36.1", p0=rec.row, p1='／'.join(reasons))))


def _v40(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("表B")
    if not rows:
        sink.set_na("V-40", "表 B 的行")
        return
    for rec in rows:
        if "scope：" in rec.get("来源证据", ""):
            sink.add_fail("V-40", line("V-40", say("l2_ref.V-40.4", p0=rec.row)))
    wanted = {}
    for rec in rows:
        if "引用 L4：" not in rec.get("主归属 / 引用", ""):
            continue
        wanted[rec.get("主键")] = (own_l4(rec.get("主归属 / 引用", "")), "、".join(ref_l4s(rec.get("主归属 / 引用", ""))))
    listing = book.logical("清单")
    table = book.tables.get("全局活动清单")
    if wanted and (table is None or not table.present):
        sink.add_fail("V-40", line("V-40", say("l2_ref.V-40.1", p0="、".join(wanted))))
        return
    if table and table.present and table.headers != ["编码", "活动名称", "主归属 L4", "引用 L4", "scope"]:
        sink.add_fail("V-40", line("V-40", say("l2_ref.V-40.2")))
    names = {rec.get("编码"): rec.get("活动名称") for rec in book.logical("表A")}
    got = {rec.get("编码"): rec for rec in listing}
    for code, rec in got.items():
        expect = wanted.get(code)
        if not expect:
            sink.add_fail("V-40", line("V-40", say("l2_ref.V-40.5", p0=code)))
            continue
        if rec.get("主归属 L4") != expect[0] or rec.get("引用 L4") != expect[1] or rec.get("scope") != "全局" or rec.get("活动名称") != names.get(code):
            sink.add_fail("V-40", line("V-40", say("l2_ref.V-40.3", p0=code)))
    missing = [code for code in wanted if code not in got]
    if missing:
        sink.add_fail("V-40", line("V-40", say("l2_ref.V-40.3", p0='、'.join(missing))))
