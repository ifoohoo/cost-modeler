# -*- coding: utf-8 -*-
"""行内检查：必填、取值域、格式，以及只看本行就能定的对应关系。"""
from __future__ import annotations

import re
from collections import defaultdict

from .load import WorkbookData
from .messages import line, say
from .model import (
    ALLOC, COL_A, DASH, ENDS, IDS, KST, MODEL_LETTERS, PAIRS, POOLS, SEG_TYPE, SRC_RANK, TABLE_A_SHEET,
    WL, Options, Sink,
)
from .textutil import D, MONEY, REF_LINE, fset, key_ok, key_problem, unkey


def _letters(cell: str, alphabet: str) -> frozenset[str]:
    """角色格的分工字母集合。空与 `—` 都是不参与；空白字符不算字母。"""
    text = (cell or "").strip()
    if text in ("", DASH):
        return frozenset()
    return frozenset(ch for ch in text if not ch.isspace())


def _v02(sink: Sink, sheet: str, rec, column: str, cond: bool = True, dash_ok: bool = False) -> None:
    if not cond:
        return
    value = rec.get(column, "")
    if value == "" or (value == DASH and not dash_ok):
        sink.add_fail("V-02", line(
            "V-02",
            say("l1_row.V-02.1", p0=sheet, p1=rec.row, p2=column),
        ))


def _v03(sink: Sink, sheet: str, rec, column: str, allowed: list[str], ok: bool | None = None) -> None:
    if ok is None:
        ok = rec.get(column, "") in allowed
    if ok:
        return
    shown = "、".join(allowed)
    sink.add_fail("V-03", line(
        "V-03",
        say("l1_row.V-03.1", p0=sheet, p1=rec.row, p2=column, p3=rec.get(column, ''), p4=shown),
    ))


def _kst(book: WorkbookData, key: str) -> str:
    token = unkey(key)
    for row in book.logical("机能"):
        if unkey(row.get("主键", "")) == token:
            return row.get("下钻状态", "")
    return ""


def run(book: WorkbookData, sink: Sink, opt: Options) -> None:
    _required(book, sink)
    _domain(book, sink)
    _unique(book, sink)
    _keys(book, sink)
    _v14(book, sink)
    _v16(book, sink)
    _v17(book, sink)
    _v18(book, sink)
    _v22(book, sink)
    _v24(book, sink)
    _v31(book, sink)
    _v32(book, sink)
    _v42(book, sink)


def _required(book: WorkbookData, sink: Sink) -> None:
    for rec in book.logical("表A"):
        for column in ("活动名称", "编码", "分工模型"):
            _v02(sink, rec.sheet, rec, column)
    for rec in book.logical("表B"):
        sheet = rec.sheet
        for column in ("主键", "输出：业务对象 + 完成后的状态", "输入：业务对象 + 进入时的状态", "主归属 / 引用", "执行方式", "来源证据"):
            _v02(sink, sheet, rec, column)
        _v02(sink, sheet, rec, "受益方留痕", rec.get("下钻状态") != "不适用")
        _v02(sink, sheet, rec, "承载系统", rec.get("执行方式") in ("线上", "并存"))
        _v02(sink, sheet, rec, "关联业务功能编号（F-）", dash_ok=True)
    for rec in book.logical("功能"):
        sheet = rec.sheet
        for column in ("主键", "功能名", "功能身份", "来源证据", "下钻状态"):
            _v02(sink, sheet, rec, column)
        _v02(sink, sheet, rec, "协同能力类型", dash_ok=True)
        for column in ("平台功能用户", "平台白名单类别"):
            _v02(sink, sheet, rec, column, rec.get("功能身份") in ("平台功能", "公共能力"))
        _v02(sink, sheet, rec, "平台对象标识", rec.get("协同能力类型") == "专属搭建", dash_ok=False)
        if rec.get("协同能力类型") != "专属搭建":
            _v02(sink, sheet, rec, "平台对象标识", dash_ok=True)
    for rec in book.logical("机能"):
        sheet = rec.sheet
        unread = rec.get("下钻状态") == "未登记"
        for column in ("主键", "下钻状态", "来源证据"):
            _v02(sink, sheet, rec, column)
        for column in ("触发方式", "实现形式", "类型"):
            _v02(sink, sheet, rec, column, not unread)
        _v02(sink, sheet, rec, "端", rec.get("类型") == "画面", dash_ok=False)
        if rec.get("类型") != "画面":
            _v02(sink, sheet, rec, "端", dash_ok=True)
        _v02(sink, sheet, rec, "主归属功能编号", rec.get("下钻状态") not in ("待下钻", "未登记"))
        _v02(sink, sheet, rec, "受益方留痕", rec.get("下钻状态") == "本质无单一归属")
        if rec.get("下钻状态") != "本质无单一归属":
            _v02(sink, sheet, rec, "受益方留痕", dash_ok=True)
    for rec in book.logical("明细"):
        sheet = rec.sheet
        for column in ("功能过程名", "数据移动序号", "数据移动类型", "数据对象", COL_A, "来源证据", "隐含读写标记", "归属层级"):
            allow_dash = column == "隐含读写标记" or (
                column == "归属层级" and not unkey(rec.get("机能主键", "")).startswith("画面|") and rec.get("共享加载画面标识") == DASH
            )
            _v02(sink, sheet, rec, column, dash_ok=allow_dash)
        _v02(sink, sheet, rec, "FUR 依据", dash_ok=True)
        _v02(sink, sheet, rec, "触发业务功能编号", _kst(book, rec.get("机能主键", "")) not in ("待下钻", "未登记") and rec.get("归属层级") != "整页级")
        if rec.get("归属层级") == "整页级" or _kst(book, rec.get("机能主键", "")) in ("待下钻", "未登记"):
            _v02(sink, sheet, rec, "触发业务功能编号", dash_ok=True)
        _v02(sink, sheet, rec, "机能主键", rec.get("归属层级") != "整页级")
        _v02(sink, sheet, rec, "共享加载画面标识", dash_ok=True)
        _v02(sink, sheet, rec, "受益方留痕", dash_ok=True)
    for rec in book.logical("汇总"):
        sheet = rec.sheet
        for column in ("主键", COL_B := "列 B 分摊后规模（归集用）", "列一 不复用", "列二 复用", "来源证据", "下钻状态"):
            _v02(sink, sheet, rec, column)
        _v02(sink, sheet, rec, "已落数据对象数", dash_ok=True)
        _v02(sink, sheet, rec, "复用声明", dash_ok=True)
        _v02(sink, sheet, rec, "受益方留痕", dash_ok=True)
    for rec in book.logical("链路"):
        for column in ("主键", "链路判定", "下钻状态", "来源证据"):
            _v02(sink, rec.sheet, rec, column)
        _v02(sink, rec.sheet, rec, "受益方留痕", dash_ok=True)
    for rec in book.logical("分摊") + (book.copy_rows or []):
        for column in ("期次", "池类型", "池发生额", "使用方业务功能", "动因", "分摊额", "来源证据", "成本池"):
            _v02(sink, rec.sheet, rec, column)
        _v02(sink, rec.sheet, rec, "使用方来源档", rec.get("动因") in ("等分（降级口径）", "CFP 消费占比"))
        _v02(sink, rec.sheet, rec, "受益方留痕", rec.get("动因") in ("等分（降级口径）", "CFP 消费占比"))
        _v02(sink, rec.sheet, rec, "下钻状态", dash_ok=True)
        _v02(sink, rec.sheet, rec, "需求编号（标签）", dash_ok=True)
    for rec in book.logical("登记簿"):
        for column in ("主键", "建设版本", "共通标记", "建设期使用方", "受益方留痕（各期使用方清单）", "来源证据", "下钻状态"):
            _v02(sink, rec.sheet, rec, column)
        _v02(sink, rec.sheet, rec, "改造历史", dash_ok=True)
    for rec in book.logical("补登"):
        for column in rec.keys():
            if column == "处理结果":
                _v02(sink, rec.sheet, rec, column, dash_ok=True)
            else:
                _v02(sink, rec.sheet, rec, column)
    for rec in book.logical("不计入"):
        for column in ("主键", "对象名称", "对象类别", "不计入原因", "投入量", "来源证据"):
            _v02(sink, rec.sheet, rec, column)
    for rec in book.logical("恒等式") + book.logical("全系统"):
        for column in ("期次", "范围", "实际成本总额", "Σ分摊额", "Σ剔除额", "来源证据"):
            _v02(sink, rec.sheet, rec, column)


def _domain(book: WorkbookData, sink: Sink) -> None:
    _domain_table_a(book, sink)
    for rec in book.logical("表B"):
        _v03(sink, rec.sheet, rec, "主归属 / 引用", ["主归属 L4：〈编码〉", "主归属 L4：〈编码〉；引用 L4：〈编码〉"], REF_LINE.fullmatch(rec.get("主归属 / 引用", "")) is not None)
        _v03(sink, rec.sheet, rec, "执行方式", ["线上", "线下", "并存"])
        _v03(sink, rec.sheet, rec, "下钻状态", ["已下钻", "待下钻", "不适用"])
        if rec.get("执行方式") == "线下":
            _v03(sink, rec.sheet, rec, "承载系统", [DASH])
        benefit = rec.get("受益方留痕", "")
        if rec.get("下钻状态") == "不适用":
            _v03(sink, rec.sheet, rec, "受益方留痕", [DASH])
        else:
            _v03(sink, rec.sheet, rec, "受益方留痕", ["等分", "权重：〈值〉；理由：〈一句话〉；指定方：〈职能〉"], benefit == "等分" or benefit.startswith("权重："))
    for rec in book.logical("功能"):
        _v03(sink, rec.sheet, rec, "功能身份", list(IDS))
        _v03(sink, rec.sheet, rec, "平台功能用户", ["治理或管理类角色", "所有已认证用户（集合）", "具体业务角色", DASH])
        _v03(sink, rec.sheet, rec, "平台白名单类别", WL + [DASH])
        _v03(sink, rec.sheet, rec, "协同能力类型", ["原生", "专属搭建", DASH])
        _v03(sink, rec.sheet, rec, "下钻状态", ["已下钻", "待下钻"])
    for rec in book.logical("机能"):
        unread = rec.get("下钻状态") == "未登记"
        trigger_ok = rec.get("触发方式") in {"用户", "调度器", "消息中间件", "服务间调用", "用户＋服务间调用"} or (unread and rec.get("触发方式") == DASH)
        _v03(sink, rec.sheet, rec, "触发方式", ["用户", "调度器", "消息中间件", "服务间调用", "用户＋服务间调用", DASH], trigger_ok)
        type_ok = rec.get("类型") in ("画面", "接口", "定时任务", "消息消费者", "事件消费") or (rec.get("类型") == DASH and unread)
        _v03(sink, rec.sheet, rec, "类型", ["画面", "接口", "定时任务", "消息消费者", "事件消费", DASH], type_ok)
        end_ok = rec.get("端") == DASH or (rec.get("端") != "" and all(item in ENDS for item in fset(rec.get("端"))))
        _v03(sink, rec.sheet, rec, "端", ENDS + [DASH], end_ok)
        _v03(sink, rec.sheet, rec, "下钻状态", list(KST))
    km = {unkey(row.get("主键", "")): row for row in book.logical("机能")}
    for rec in book.logical("明细"):
        _v03(sink, rec.sheet, rec, "数据移动类型", ["E", "X", "R", "W"], rec.get("数据移动类型") in "EXRW" and len(rec.get("数据移动类型", "")) == 1)
        _v03(sink, rec.sheet, rec, "归属层级", ["整页级", "区块级", DASH])
        _v03(sink, rec.sheet, rec, "隐含读写标记", ["权限读", "审计写", DASH])
        if rec.get("归属层级") == "整页级":
            _v03(sink, rec.sheet, rec, "下钻状态", [DASH])
        else:
            _v03(sink, rec.sheet, rec, "下钻状态", list(KST))
        _v03(sink, rec.sheet, rec, "受益方留痕", [DASH])
        amount = rec.get(COL_A, "")
        _v03(sink, rec.sheet, rec, COL_A, ["非负数字"], re.fullmatch(r"\d+(?:\.\d+)?", amount or "") is not None)
    _sequences(book, sink)
    for rec in book.logical("汇总"):
        for column in ("列 B 分摊后规模（归集用）", "列一 不复用", "列二 复用"):
            _v03(sink, rec.sheet, rec, column, ["非负数字"], re.fullmatch(r"\d+(?:\.\d+)?", rec.get(column, "") or "") is not None)
    for rec in book.logical("链路"):
        _v03(sink, rec.sheet, rec, "功能身份", list(IDS) + [DASH])
        _v03(sink, rec.sheet, rec, "链路判定", ["不要求", "缺功能", "缺活动", "缺子流程", "完整"])
        _v03(sink, rec.sheet, rec, "下钻状态", list(KST))
        _v03(sink, rec.sheet, rec, "来源证据", ["机器导出：链路核对"])
        _v03(sink, rec.sheet, rec, "受益方留痕", [DASH])
    for rec in list(book.logical("分摊")) + list(book.copy_rows or []):
        pool = rec.get("池类型", "")
        cost = unkey(rec.get("成本池", ""))
        _v03(sink, rec.sheet, rec, "池类型", list(POOLS))
        if pool == "直接成本":
            cost_ok = key_ok(cost) or cost.startswith("外购调用：")
        elif pool == "共享池":
            cost_ok = key_ok(cost) or cost.startswith("归挂：") or cost.startswith("外购调用：")
        elif pool == "共享服务池":
            cost_ok = cost.startswith("共享服务：") and len(cost) > len("共享服务：")
        elif pool == "未下钻池":
            cost_ok = key_ok(cost)
        elif pool in ("公共池", "平台池"):
            cost_ok = key_ok(cost) or F_OK(cost)
        else:
            cost_ok = False
        _v03(sink, rec.sheet, rec, "成本池", ["机能主键", "归挂：〈名称〉", "外购调用：〈服务名〉", "共享服务：〈服务名〉", "F 编号"], cost_ok)
        _v03(sink, rec.sheet, rec, "使用方来源档", list(SRC_RANK) + [DASH])
        _v03(sink, rec.sheet, rec, "动因", list(ALLOC))
        _v03(sink, rec.sheet, rec, "池发生额", ["到分的金额"], MONEY.fullmatch(rec.get("池发生额", "") or "") is not None)
        _v03(sink, rec.sheet, rec, "分摊额", ["到分的金额"], MONEY.fullmatch(rec.get("分摊额", "") or "") is not None)
        if pool == "未下钻池":
            want = "待下钻"
        elif pool in ("公共池", "平台池"):
            want = "已下钻"
        elif pool == "共享服务池":
            want = DASH
        elif cost.startswith("外购调用：") or cost.startswith("归挂："):
            want = "已下钻"
        else:
            known = km.get(cost)
            want = known.get("下钻状态") if known else ""
        if want:
            _v03(sink, rec.sheet, rec, "下钻状态", [want], rec.get("下钻状态") == want and rec.get("下钻状态") != "未登记")
    for rec in book.logical("登记簿"):
        _v03(sink, rec.sheet, rec, "共通标记", ["潜在共通能力", "共通能力"])
        _v03(sink, rec.sheet, rec, "下钻状态", list(KST))
    for rec in book.logical("补登"):
        _v03(sink, rec.sheet, rec, "表 A 检索结果", ["无命中", "命中且三元组全等", "命中但角色不同"])
        _v03(sink, rec.sheet, rec, "三问结论", ["过/过/过 这类三段"], re.fullmatch(r"(过|不过)/(过|不过)/(过|不过)", rec.get("三问结论", "")) is not None)
        result = rec.get("处理结果", "")
        result_ok = result in ("不许补", "已撤销", DASH) or re.fullmatch(r"已补入表 A：\S+", result) is not None
        _v03(sink, rec.sheet, rec, "处理结果", ["已补入表 A：〈编码〉", "不许补", "已撤销", DASH], result_ok)
    for rec in book.logical("不计入"):
        _v03(sink, rec.sheet, rec, "对象类别", ["无法归挂的内部逻辑", "宏", "模板", "插件", "线下工时", "进池前剔除"])
        reason = rec.get("不计入原因", "")
        _v03(sink, rec.sheet, rec, "不计入原因", ["入口为零：", "未过准入：①", "未过准入：②", "不计入报价：", "他系统份额：", "他系统接入："], re.match(r"(入口为零：|未过准入：[①②]|不计入报价：|他系统份额：|他系统接入：)", reason) is not None)
        _v03(sink, rec.sheet, rec, "投入量", ["到分的金额"], MONEY.fullmatch(rec.get("投入量", "") or "") is not None)
        _v03(sink, rec.sheet, rec, "来源证据", ["含期次："], "期次：" in rec.get("来源证据", ""))
    l4s = {code.rsplit(".", 1)[0] for code in (row.get("编码", "") for row in book.logical("表A")) if code}
    for rec in book.logical("恒等式") + book.logical("全系统"):
        for column in ("实际成本总额", "Σ分摊额", "Σ剔除额"):
            _v03(sink, rec.sheet, rec, column, ["到分的金额"], MONEY.fullmatch(rec.get(column, "") or "") is not None)
        scope = rec.get("范围", "")
        _v03(sink, rec.sheet, rec, "范围", ["本片合计"] + sorted(l4s), scope == "本片合计" or scope in l4s)
        if scope == "本片合计":
            _v03(sink, rec.sheet, rec, "来源证据", ["人工认定：…", "机器导出：…"], re.match(r"(人工认定|机器导出)：\S", rec.get("来源证据", "")) is not None)
        else:
            _v03(sink, rec.sheet, rec, "来源证据", ["机器算：本分表 Σ分摊额"])


def _domain_table_a(book: WorkbookData, sink: Sink) -> None:
    """分工模型枚举 + 角色格字母按本行模型的字母表逐一校验，同一字母一格内不重复，空与 `—` 合法。"""
    table = book.tables.get(TABLE_A_SHEET)
    roles = table.role_headers if table else []
    for rec in book.logical("表A"):
        model = rec.get("分工模型", "")
        _v03(sink, rec.sheet, rec, "分工模型", list(MODEL_LETTERS))
        alphabet = MODEL_LETTERS.get(model)
        if alphabet is None:
            continue
        allowed = "、".join(alphabet) + " 的组合"
        for role in roles:
            cell = rec.get(role, "")
            text = cell.strip()
            if text in ("", DASH):
                continue
            letters = [ch for ch in text if not ch.isspace()]
            ok = bool(letters) and all(ch in alphabet for ch in letters) and len(set(letters)) == len(letters) and "".join(letters) == text
            _v03(sink, rec.sheet, rec, role, [allowed], ok)


def _v42(book: WorkbookData, sink: Sink) -> None:
    """角色分工风险：多 R、多 A、任务型缺 R/缺 A、会议型缺 O/缺 R/缺 A，全部只预警。
    同一角色格含多个字母（如 `AR`）是合法写法，不进本项。"""
    rows = book.logical("表A")
    if not rows:
        sink.set_na("V-42", "表 A 的角色分配行")
        return
    table = book.tables.get(TABLE_A_SHEET)
    roles = table.role_headers if table else []
    tail = say("frag.004")
    for rec in rows:
        model = rec.get("分工模型", "")
        alphabet = MODEL_LETTERS.get(model)
        if alphabet is None:
            continue
        cells = {role: _letters(rec.get(role, ""), alphabet) for role in roles}
        holders = {letter: [role for role in roles if letter in cells[role]] for letter in alphabet}
        if len(holders.get("R", [])) > 1:
            sink.add_warn("V-42", line(
                "V-42",
                say("l1_row.V-42.1", p0=rec.row, p1='、'.join(holders['R']), p2=tail),
            ))
        if len(holders.get("A", [])) > 1:
            sink.add_warn("V-42", line(
                "V-42",
                say("l1_row.V-42.2", p0=rec.row, p1='、'.join(holders['A']), p2=tail),
            ))
        if model == "任务型":
            missing = []
            if not holders.get("R"):
                missing.append(say("frag.005"))
            if not holders.get("A"):
                missing.append(say("frag.006"))
            if missing:
                sink.add_warn("V-42", line("V-42", say("l1_row.V-42.3", p0=rec.row, p1='／'.join(missing), p2=tail)))
        if model == "会议型":
            missing = []
            if not holders.get("O"):
                missing.append(say("frag.007"))
            if not holders.get("R"):
                missing.append(say("frag.008"))
            if not holders.get("A"):
                missing.append(say("frag.009"))
            if missing:
                sink.add_warn("V-42", line("V-42", say("l1_row.V-42.4", p0=rec.row, p1='／'.join(missing), p2=tail)))


def _process_key(rec) -> tuple[str, str, str]:
    """同一功能过程的序号连在一起。共享加载按画面标识把整页行和区块行合成一组。"""
    name = rec.get("功能过程名", "")
    shared = rec.get("共享加载画面标识", "")
    machine = unkey(rec.get("机能主键", ""))
    if shared not in ("", DASH):
        return ("屏", shared, name)
    if machine.startswith("画面|") and "|" in machine:
        host = machine.split("|", 2)[1]
        return ("屏", host.split(" ", 1)[0], name)
    return ("机", machine, name)


def _sequences(book: WorkbookData, sink: Sink) -> None:
    grouped = defaultdict(list)
    for rec in book.logical("明细"):
        grouped[_process_key(rec)].append(rec)
    allowed = ["从 1 开始的连续正整数"]
    for rows in grouped.values():
        numbers = []
        parsed = True
        for rec in rows:
            text = str(rec.get("数据移动序号", ""))
            if re.fullmatch(r"[1-9]\d*", text) is None:
                parsed = False
                break
            numbers.append(int(text))
        if parsed and sorted(numbers) == list(range(1, len(rows) + 1)):
            continue
        for rec in rows:
            _v03(sink, rec.sheet, rec, "数据移动序号", allowed, False)


def F_OK(value: str) -> bool:
    return re.fullmatch(r"F-[A-Za-z0-9.\-]+", value or "") is not None


def _unique(book: WorkbookData, sink: Sink) -> None:
    def uniq(sheet_label, rows, keyfn):
        seen = defaultdict(list)
        for rec in rows:
            seen[keyfn(rec)].append(rec)
        for key, group in seen.items():
            if len(group) < 2 or key in ("", None):
                continue
            numbers = [rec.row for rec in group]
            sheet = group[0].sheet
            sink.add_fail("V-04", line(
                "V-04",
                say("l1_row.V-04.1", p0=sheet, p1='、'.join(str(number) for number in numbers), p2=key),
            ))

    uniq("表A", book.logical("表A"), lambda rec: rec.get("编码", ""))
    uniq("表B", book.logical("表B"), lambda rec: rec.get("主键", ""))
    uniq("功能", book.logical("功能"), lambda rec: rec.get("主键", ""))
    uniq("机能", book.logical("机能"), lambda rec: unkey(rec.get("主键", "")))
    uniq("明细", book.logical("明细"), lambda rec: (
        unkey(rec.get("机能主键")) if rec.get("机能主键") != DASH else rec.get("共享加载画面标识"),
        rec.get("功能过程名"),
        str(rec.get("数据移动序号")),
    ))
    uniq("汇总", book.logical("汇总"), lambda rec: unkey(rec.get("主键", "")))
    uniq("链路", book.logical("链路"), lambda rec: unkey(rec.get("主键", "")))
    uniq("分摊", book.logical("分摊"), lambda rec: (rec.get("期次"), rec.get("池类型"), unkey(rec.get("成本池")), rec.get("使用方业务功能")))
    uniq("登记簿", book.logical("登记簿"), lambda rec: (unkey(rec.get("主键")), rec.get("建设版本")))
    uniq("补登", book.logical("补登"), lambda rec: str(rec.get("主键")))
    uniq("不计入", book.logical("不计入"), lambda rec: str(rec.get("主键")))
    uniq("恒等式", book.logical("恒等式") + book.logical("全系统"), lambda rec: (rec.get("期次"), rec.get("范围"), rec.sheet))


def _keys(book: WorkbookData, sink: Sink) -> None:
    cells = []
    for rec in book.logical("机能") + book.logical("汇总") + book.logical("链路") + book.logical("登记簿"):
        cells.append((rec, "主键", rec.get("主键", "")))
    for rec in book.logical("明细"):
        if rec.get("机能主键") != DASH:
            cells.append((rec, "机能主键", rec.get("机能主键", "")))
    for rec in book.logical("分摊"):
        cost = unkey(rec.get("成本池", ""))
        if rec.get("池类型") in ("直接成本", "共享池", "未下钻池", "公共池", "平台池") and not cost.startswith(("归挂：", "外购调用：", "共享服务：")) and not F_OK(cost):
            cells.append((rec, "成本池", rec.get("成本池", "")))
    for rec in book.logical("补登"):
        token = unkey(rec.get("触发来源", ""))
        if token == "" or F_OK(token):
            continue
        cells.append((rec, "触发来源", rec.get("触发来源", "")))
    for rec, column, value in cells:
        problem = key_problem(value)
        if not problem:
            continue
        sink.add_fail("V-05", line(
            "V-05",
            say("l1_row.V-05.1", p0=rec.sheet, p1=rec.row, p2=unkey(value), p3=problem),
        ))


def _v14(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("功能")
    if not rows:
        return
    seen = defaultdict(list)
    for rec in rows:
        if rec.get("协同能力类型") == "原生":
            sink.add_fail("V-14", line("V-14", say("l1_row.V-14.1", p0=rec.row)))
        if rec.get("协同能力类型") == "专属搭建" and not ("独立责任方：" in rec.get("来源证据", "") and "变更记录编号：" in rec.get("来源证据", "")):
            sink.add_fail("V-14", line("V-14", say("l1_row.V-14.2", p0=rec.row)))
        marker = rec.get("平台对象标识", "")
        if rec.get("协同能力类型") == "专属搭建":
            items = fset(marker)
            good = []
            for item in items:
                host = re.fullmatch(r"宿主：\S+ \S+", item)
                side = re.fullmatch(r"附属：(字段校验|审批人设置|权限|菜单挂接) \S+", item)
                good.append(bool(host or side))
            if not items or not all(good):
                sink.add_fail("V-14", line("V-14", say("l1_row.V-14.4", p0=rec.row)))
            elif all(item.startswith("附属：") for item in items):
                sink.add_fail("V-14", line("V-14", say("l1_row.V-14.6", p0=rec.row)))
            if len(set(items)) != len(items):
                sink.add_fail("V-14", line("V-14", say("l1_row.V-14.3", p0=rec.row)))
            for item in set(items):
                seen[item].append(rec)
        elif marker != DASH:
            sink.add_fail("V-14", line("V-14", say("l1_row.V-14.5", p0=rec.row)))
    for item, group in seen.items():
        if len(group) > 1:
            numbers = "、".join(str(rec.row) for rec in group)
            sink.add_fail("V-14", line("V-14", say("l1_row.V-14.3", p0=numbers)))


def _v16(book: WorkbookData, sink: Sink) -> None:
    for rec in book.logical("机能"):
        if rec.get("类型") == DASH:
            if rec.get("下钻状态") != "未登记":
                sink.add_fail("V-16", line("V-16", say("l1_row.V-16.1", p0=rec.row, p1=rec.get('触发方式'), p2=rec.get('类型'))))
            continue
        if (rec.get("触发方式"), rec.get("类型")) not in PAIRS:
            sink.add_fail("V-16", line("V-16", say("l1_row.V-16.1", p0=rec.row, p1=rec.get('触发方式'), p2=rec.get('类型'))))
        segment = unkey(rec.get("主键", "")).split("|")[0] if unkey(rec.get("主键", "")) else ""
        if SEG_TYPE.get(segment) != rec.get("类型"):
            sink.add_fail("V-16", line("V-16", say("l1_row.V-16.2", p0=rec.row, p1=segment, p2=rec.get('类型'))))


def _v17(book: WorkbookData, sink: Sink) -> None:
    for rec in book.logical("机能"):
        if rec.get("类型") == "画面":
            ends = fset(rec.get("端"))
            if not ends or not all(item in ENDS for item in ends):
                sink.add_fail("V-17", line("V-17", say("l1_row.V-17.1", p0=rec.row, p1=rec.get('端'))))
        elif rec.get("端") != DASH:
            sink.add_fail("V-17", line("V-17", say("l1_row.V-17.2", p0=rec.row)))


def _v18(book: WorkbookData, sink: Sink) -> None:
    for rec in book.logical("机能"):
        if rec.get("类型") != "画面":
            continue
        evidence = rec.get("来源证据", "")
        matched = re.search(r"结果区：([^；]*)", evidence)
        if not ("区块业务目的：" in evidence and "输入区：" in evidence and matched and matched.group(1).strip() not in ("", DASH)):
            sink.add_fail("V-18", line("V-18", say("l1_row.V-18.1", p0=rec.row)))


def _v22(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("明细")
    if not rows:
        sink.set_na("V-22", "数据移动明细的行")
        return
    known = {unkey(rec.get("主键", "")) for rec in book.logical("机能")}
    for rec in rows:
        machine = rec.get("机能主键", "")
        shared = rec.get("共享加载画面标识", "")
        level = rec.get("归属层级", "")
        reasons = []
        if (machine != DASH) == (shared != DASH):
            reasons.append(say("frag.010"))
        if (shared != DASH) != (level == "整页级"):
            reasons.append(say("frag.011"))
        is_screen = machine != DASH and unkey(machine).startswith("画面|")
        if rec.get("数据移动类型") == "X" and (is_screen or shared != DASH) and level != "区块级":
            reasons.append(say("frag.012"))
        if machine != DASH and unkey(machine) not in known:
            reasons.append(say("frag.013"))
        if machine != DASH:
            if is_screen and not (level == "区块级" and "只服务：" in rec.get("来源证据", "")):
                reasons.append(say("frag.014"))
            if not is_screen and level != DASH:
                reasons.append(say("frag.015"))
        if reasons:
            sink.add_fail("V-22", line("V-22", say("l1_row.V-22.1", p0=rec.row, p1='／'.join(reasons))))


def _v24(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("明细")
    if not rows:
        sink.set_na("V-24", "数据移动明细的行")
        return
    for rec in rows:
        mark = rec.get("隐含读写标记", "")
        reasons = []
        if (mark == "权限读" and rec.get("数据移动类型") != "R") or (mark == "审计写" and rec.get("数据移动类型") != "W"):
            reasons.append(say("frag.016"))
        if mark != DASH and rec.get("FUR 依据") == DASH and D(rec.get(COL_A)) != 0:
            reasons.append(say("frag.017"))
        if reasons:
            sink.add_fail("V-24", line("V-24", say("l1_row.V-22.1", p0=rec.row, p1='／'.join(reasons))))


def _pool_groups(book: WorkbookData):
    groups = defaultdict(list)
    for rec in book.logical("分摊"):
        groups[(rec.get("期次"), rec.get("池类型"), unkey(rec.get("成本池")))].append(rec)
    return groups


def _v31(book: WorkbookData, sink: Sink) -> None:
    rows = book.logical("分摊")
    if not rows:
        sink.set_na("V-31", "分摊表的行")
        return
    functions = {rec.get("主键"): rec for rec in book.logical("功能")}
    machines = {unkey(rec.get("主键")): rec for rec in book.logical("机能")}
    for rec in rows:
        pool = rec.get("池类型")
        if pool not in ("公共池", "平台池"):
            continue
        want = "平台功能" if pool == "平台池" else "公共能力"
        cost = unkey(rec.get("成本池"))
        if key_ok(cost):
            machine = machines.get(cost)
            owner = machine.get("主归属功能编号") if machine else DASH
            if not machine or owner not in functions or functions[owner].get("功能身份") != want:
                sink.add_fail("V-31", line("V-31", say("l1_row.V-31.3", p0=rec.row, p1=pool, p2=rec.get('动因'))))
                # 身份不对用同一处理口径里的「该行不合格」，问题句改回身份。
                sink.fail["V-31"].pop()
                sink.add_fail("V-31", line("V-31", say("l1_row.V-31.4", p0=rec.row, p1=pool, p2=want)))
        elif F_OK(cost):
            if cost not in functions or functions[cost].get("功能身份") != want or any(item.get("主归属功能编号") == cost for item in book.logical("机能")):
                sink.add_fail("V-31", line("V-31", say("l1_row.V-31.4", p0=rec.row, p1=pool, p2=want)))
        else:
            sink.add_fail("V-31", line("V-31", say("l1_row.V-31.5", p0=rec.row, p1=pool)))
    for (_period, pool, cost), group in _pool_groups(book).items():
        drivers = {rec.get("动因") for rec in group}
        if len(drivers) > 1:
            numbers = "、".join(str(rec.row) for rec in group)
            sink.add_fail("V-31", line("V-31", say("l1_row.V-31.1", p0=numbers, p1=group[0].get('期次'), p2=pool, p3=cost)))
        for rec in group:
            driver = rec.get("动因")
            if pool == "直接成本" and driver != "直接归属":
                sink.add_fail("V-31", line("V-31", say("l1_row.V-31.6", p0=rec.row, p1=driver)))
            elif pool == "直接成本" and D(rec.get("分摊额")) != D(rec.get("池发生额")):
                sink.add_fail("V-31", line("V-31", say("l1_row.V-31.9", p0=rec.row, p1=rec.get('分摊额'), p2=rec.get('池发生额'))))
            if pool == "共享池":
                allowed = ("调用量占比", "等分（降级口径）") if str(cost).startswith("外购调用：") else ("CFP 消费占比", "等分（降级口径）")
                if driver not in allowed:
                    sink.add_fail("V-31", line("V-31", say("l1_row.V-31.10", p0=rec.row, p1='、'.join(allowed), p2=driver)))
                if driver == "调用量占比" and not str(cost).startswith("外购调用："):
                    sink.add_fail("V-31", line("V-31", say("l1_row.V-31.11", p0=rec.row, p1=pool, p2='、'.join(allowed), p3=driver)))
            if pool in ("公共池", "平台池") and driver not in ("CFP 消费占比", "等分（降级口径）", "全盘业务 CFP 占比"):
                sink.add_fail("V-31", line("V-31", say("l1_row.V-31.3", p0=rec.row, p1=pool, p2=driver)))
            if pool == "未下钻池" and driver != "全盘业务 CFP 占比":
                sink.add_fail("V-31", line("V-31", say("l1_row.V-31.7", p0=rec.row, p1=driver)))
            if pool == "共享服务池" and driver != "全盘业务 CFP 占比":
                sink.add_fail("V-31", line("V-31", say("l1_row.V-31.8", p0=rec.row, p1=driver)))
        if pool == "共享池" and len(group) < 2:
            sink.add_fail("V-31", line("V-31", say("l1_row.V-31.2", p0=group[0].row, p1=group[0].get('期次'), p2=pool, p3=cost)))


def _v32(book: WorkbookData, sink: Sink) -> None:
    rows = [rec for rec in book.logical("分摊") if rec.get("池类型") != "未下钻池" and rec.get("动因") in ("等分（降级口径）", "CFP 消费占比")]
    if not rows:
        sink.set_na("V-32", "要查等分或消费占比证据的行")
        return
    groups = _pool_groups(book)
    undrilled = {(rec.get("期次"), unkey(rec.get("成本池"))) for rec in book.logical("分摊") if rec.get("池类型") == "未下钻池"}
    for rec in rows:
        trace = rec.get("受益方留痕", "")
        reasons = []
        split_gap = False
        if rec.get("使用方来源档") == DASH:
            reasons.append(say("frag.018"))
        if "主张方：" not in trace or "查过：" not in trace:
            reasons.append(say("frag.019"))
        if rec.get("使用方来源档") == "人工认定" and "查不到：" not in trace:
            reasons.append(say("frag.020"))
        if rec.get("使用方来源档") == "基线调用链" and not unkey(rec.get("成本池")).startswith("归挂："):
            reasons.append(say("frag.021"))
        if rec.get("池类型") == "共享池" and (rec.get("期次"), unkey(rec.get("成本池"))) in undrilled and "切分：已指名" not in trace:
            reasons.append(say("frag.022"))
            split_gap = True
        if not reasons:
            continue
        pool = rec.get("池类型")
        if split_gap:
            action = say("frag.023")
        elif pool == "共享池":
            action = say("frag.024")
        elif pool in ("公共池", "平台池"):
            action = say("frag.025")
        else:
            action = say("frag.026")
        sink.add_fail("V-32", line("V-32", say("l1_row.V-32.1", p0=rec.row, p1='／'.join(reasons), p2=action)))
    for (_period, pool, cost), group in groups.items():
        if pool == "未下钻池":
            continue
        picked = [rec for rec in group if rec.get("动因") in ("等分（降级口径）", "CFP 消费占比")]
        if len({rec.get("使用方来源档") for rec in picked}) > 1:
            numbers = "、".join(str(rec.row) for rec in picked)
            action = say("frag.024") if pool == "共享池" else say("frag.025")
            sink.add_fail("V-32", line("V-32", say("l1_row.V-32.2", p0=numbers, p1=action)))
