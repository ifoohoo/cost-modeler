# -*- coding: utf-8 -*-
"""表名、表头、检查项名称。表头与成本核算表格模板第 2 行逐字一致。"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

DASH = "—"
SEPARATOR_PREFIX = "以下为教学案例示例"

# 模板里要按表校验的 sheet。说明、整页级份额是读本，不参与行校验。
TEMPLATE_SHEETS = [
    "表 A 活动明细表",
    "表 B 成本侧活动扩展表",
    "流程补登清单",
    "功能登记表",
    "机能登记表",
    "不计入投入清单",
    "功能点计算表·数据移动明细",
    "功能点计算表·机能规模汇总",
    "链路核对视图",
    "分摊表",
    "能力登记簿",
    "成本恒等式",
]

HEADERS = {
    "表 B 成本侧活动扩展表": ["主键", "输出：业务对象 + 完成后的状态", "输入：业务对象 + 进入时的状态", "主归属 / 引用", "执行方式", "承载系统", "关联业务功能编号（F-）", "下钻状态", "来源证据", "受益方留痕"],
    "流程补登清单": ["主键", "候选活动名称", "执行角色", "触发来源", "表 A 检索结果", "输出：业务对象 + 完成后的状态", "拟挂业务功能编号（F-）", "三问结论", "处理结果", "来源证据"],
    "功能登记表": ["主键", "功能名", "功能身份", "平台功能用户", "平台白名单类别", "协同能力类型", "平台对象标识", "出现模块", "下钻状态", "来源证据", "受益方留痕"],
    "机能登记表": ["主键", "触发方式", "实现形式", "类型", "端", "主归属功能编号", "下钻状态", "来源证据", "受益方留痕"],
    "不计入投入清单": ["主键", "对象名称", "对象类别", "不计入原因", "投入量", "来源证据"],
    "功能点计算表·数据移动明细": ["机能主键", "共享加载画面标识", "功能过程名", "数据移动序号", "数据移动类型", "数据对象", "归属层级", "列 A 原始规模（不拆分）", "隐含读写标记", "FUR 依据", "触发业务功能编号", "需求编号（标签）", "下钻状态", "来源证据", "受益方留痕"],
    "功能点计算表·机能规模汇总": ["主键", "已落数据对象数", "列 B 分摊后规模（归集用）", "列一 不复用", "复用声明", "列二 复用", "下钻状态", "来源证据", "受益方留痕"],
    "链路核对视图": ["主键", "主归属功能编号", "功能身份", "关联活动编码", "所在 L4", "链路判定", "下钻状态", "来源证据", "受益方留痕"],
    "分摊表": ["期次", "池类型", "成本池", "池发生额", "使用方业务功能", "使用方来源档", "动因", "分摊额", "需求编号（标签）", "下钻状态", "来源证据", "受益方留痕"],
    "能力登记簿": ["主键", "建设版本", "共通标记", "建设期使用方", "受益方留痕（各期使用方清单）", "改造历史", "下钻状态", "来源证据"],
    "成本恒等式": ["期次", "范围", "实际成本总额", "Σ分摊额", "Σ剔除额", "来源证据"],
    "全局活动清单": ["编码", "活动名称", "主归属 L4", "引用 L4", "scope"],
}

# 表 A 双行表头：第 2 行分组、第 3 行列名。固定信息列 11 列逐字，角色列插在第 5 列「分工模型」之后。
TABLE_A_SHEET = "表 A 活动明细表"
TABLE_A_INFO = ["阶段", "序号", "活动名称", "编码", "分工模型", "协同资源", "输入", "输出", "KCP", "状态", "活动说明"]
TABLE_A_GROUP = "角色分工"
TABLE_A_HEAD = 5  # 前 5 列固定，其后是角色列
TABLE_A_TAIL = 6  # 角色列之后还有 6 列固定信息列
MODEL_LETTERS = {"任务型": "RASCI", "会议型": "OARP"}

# 逻辑表名 → 模板 sheet。分摊表另收「分摊表·〈L4〉」。
LOGICAL_SHEET = {
    "表A": "表 A 活动明细表",
    "表B": "表 B 成本侧活动扩展表",
    "补登": "流程补登清单",
    "功能": "功能登记表",
    "机能": "机能登记表",
    "不计入": "不计入投入清单",
    "明细": "功能点计算表·数据移动明细",
    "汇总": "功能点计算表·机能规模汇总",
    "链路": "链路核对视图",
    "分摊": "分摊表",
    "登记簿": "能力登记簿",
    "恒等式": "成本恒等式",
    "清单": "全局活动清单",
    "全系统": "全系统成本恒等式",
    "副本": "已结期次留存副本",
}

CHECK_NAME = {
    "V-00": "模版结构",
    "V-01": "表头一致",
    "V-02": "必填列非空",
    "V-03": "取值域",
    "V-04": "主键唯一",
    "V-05": "三段式主键格式",
    "V-06": "机器导出名录核对",
    "V-07": "表 B 主键能在表 A 查到",
    "V-08": "关联的 F 编号存在且是业务功能",
    "V-09": "引用 L4 合法",
    "V-10": "活动下钻状态重算",
    "V-11": "表 A 版本对比",
    "V-12": "流程补登清单",
    "V-13": "平台/公共身份证据",
    "V-14": "协同能力类型",
    "V-15": "功能下钻状态重算",
    "V-16": "触发方式与类型对应",
    "V-17": "端的取值",
    "V-18": "画面来源证据三段",
    "V-19": "机能下钻状态重算",
    "V-20": "受益方留痕",
    "V-21": "主归属功能编号",
    "V-22": "数据移动明细页结构",
    "V-23": "共享加载画面标识",
    "V-24": "隐含读写标记",
    "V-25": "触发业务功能编号一致",
    "V-26": "列 A 列 B 尾差",
    "V-27": "列一列二与复用声明",
    "V-28": "链路核对视图对机能登记表",
    "V-29": "状态检查（正常态/关账）",
    "V-30": "分摊表使用方合法",
    "V-31": "池类型对动因",
    "V-32": "等分/消费占比的证据",
    "V-33": "池重算",
    "V-34": "已结期次留存副本比对",
    "V-35": "平台功能占比",
    "V-36": "能力登记簿",
    "V-37": "关账校验",
    "V-38": "成本恒等式",
    "V-39": "工时折算",
    "V-40": "全局活动清单",
    "V-41": "接入与他系统接入",
    "V-42": "角色分工风险",
}

CHECK_ORDER = sorted(CHECK_NAME, key=lambda c: int(c.split("-")[1]))

# 不适用一句里的检查对象。
NA_OBJECT = {
    "V-09": "引用 L4 的行",
    "V-12": "流程补登清单的行",
    "V-20": "「本质无单一归属」的机能行",
    "V-32": "要查等分或消费占比证据的行",
    "V-33": "需要重算的池",
    "V-34": "已结期次的行",
    "V-36": "能力登记簿的行",
    "V-38": "分摊或不计入投入的期次",
    "V-39": "工时折算行",
    "V-41": "写了接入或他系统接入的行",
    "V-42": "表 A 的角色分配行",
}

ENDS = ["PC", "iOS", "Android", "车机", "手表", "大屏", "跨平台"]
WL = [
    "1 身份认证与单点登录",
    "2 授权与访问控制",
    "3 审计日志与安全合规",
    "4 系统参数、数据字典、基础配置",
    "5 基础技术设施",
    "6 监控、告警、运维控制台",
    "7 个性化与易用性",
]
PAIRS = {
    ("用户", "画面"),
    ("用户", "接口"),
    ("服务间调用", "接口"),
    ("用户＋服务间调用", "接口"),
    ("调度器", "定时任务"),
    ("消息中间件", "消息消费者"),
    ("消息中间件", "事件消费"),
}
SEG_TYPE = {"画面": "画面", "接口": "接口", "消费者": "消息消费者", "定时": "定时任务", "事件": "事件消费"}
KST = ("已下钻", "待下钻", "本质无单一归属", "未登记")
POOLS = ("直接成本", "共享池", "公共池", "平台池", "共享服务池", "未下钻池")
ALLOC = ("直接归属", "CFP 消费占比", "等分（降级口径）", "全盘业务 CFP 占比", "调用量占比")
NONKEY = ("归挂：", "外购调用：", "共享服务：")
IDS = ("业务功能", "平台功能", "公共能力", "数据功能")
SRC_RANK = ("基线调用链", "接口契约", "菜单-功能映射", "事件订阅表", "人工认定")
COL_A = "列 A 原始规模（不拆分）"
COL_B = "列 B 分摊后规模（归集用）"
COL_1 = "列一 不复用"
COL_2 = "列二 复用"
Q2 = Decimal("0.01")
EXPORT_FILES = ("API清单", "定时任务配置", "监听器清单", "页面路由")
EXPORT_SOURCE = {
    "OpenAPI 清单": "API清单",
    "API 清单": "API清单",
    "API清单": "API清单",
    "定时任务配置": "定时任务配置",
    "监听器清单": "监听器清单",
    "页面路由": "页面路由",
}

LLM_PROMPT = """你在复核一套成本核算表格里的措辞疑点。规则只有两条：
1. 业务侧的文字（活动名称、输入、输出、区块业务目的）必须说业务，不许出现系统实现名词：表名、字段名、类名、方法名、工具名、接口路径、英文标识符。
2. 证据叙述必须说得清：「非业务功能理由」要说明为什么它不是业务功能；「区块业务目的」要说明这块给业务交出什么结果。

下面是脚本筛出的候选行（JSON）。逐条复核，输出 JSON 数组，每条含：表名、行号、列名、疑点类别（业务语义红线／证据叙述不清／沿用措辞含糊）、一句问题说明、建议改法。拿不准的标「拿不准」，不许编造表格里没有的内容。没有疑点的行不进输出。"""


class Rec(dict):
    def __init__(self, data, row: int, sheet: str, case: str | None = None, period: str | None = None):
        super().__init__(data)
        self.row = row
        self.sheet = sheet
        self.case = case
        self.period = period

    def __missing__(self, key):
        return ""


@dataclass
class Table:
    name: str
    headers: list[str]
    rows: list[Rec] = field(default_factory=list)
    present: bool = True
    separator_missing: bool = False
    header_bad: bool = False
    role_cols: list[int] = field(default_factory=list)  # 表 A：角色列的 1 起始列号
    role_group_found: bool = True  # 表 A：分组行里是否找到「角色分工」

    @property
    def blocked(self) -> bool:
        return (not self.present) or self.separator_missing or self.header_bad

    @property
    def role_headers(self) -> list[str]:
        return [self.headers[col - 1] for col in self.role_cols if 0 < col <= len(self.headers)]


@dataclass
class Options:
    state: str = "正常态"
    closing: bool = False
    warn: Decimal = Decimal("0.10")
    limit: Decimal = Decimal("0.15")
    scale_digits: int = 4

    @property
    def scale_q(self) -> Decimal:
        return Decimal(1).scaleb(-self.scale_digits)


@dataclass
class Sink:
    fail: dict[str, list[str]] = field(default_factory=dict)
    warn: dict[str, list[str]] = field(default_factory=dict)
    na: dict[str, str] = field(default_factory=dict)
    unable: dict[str, list[str]] = field(default_factory=dict)
    skip: dict[str, str] = field(default_factory=dict)

    def add_fail(self, code: str, text: str) -> None:
        self.fail.setdefault(code, []).append(text)

    def add_warn(self, code: str, text: str) -> None:
        self.warn.setdefault(code, []).append(text)

    def set_na(self, code: str, obj: str) -> None:
        self.na[code] = obj

    def set_unable(self, code: str, text: str) -> None:
        self.unable.setdefault(code, []).append(text)

    def set_skip(self, code: str, obj: str) -> None:
        self.skip[code] = obj
