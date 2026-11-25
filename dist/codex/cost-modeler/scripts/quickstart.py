# -*- coding: utf-8 -*-
"""按人说的话指到检查或填写引导。自己不跑校验，也不代填。

<!-- @feature CM4 -->
"""
from __future__ import annotations

import argparse

_FILL = ("不会填", "怎么填", "填写", "填哪", "这一格", "不确定")
_CHECK = ("检查", "校验", "报告", "复跑")
_OUTSIDE = ("删除", "安装", "改工作簿", "改单元格", "联网", "别的技能")


def classify(text: str) -> dict:
    """一句话只对应一个入口时给出入口名。两件事同时出现，或夹着本族不做的动作时，停下来问清。"""
    outside = [word for word in _OUTSIDE if word in text]
    if outside:
        return {"kind": "limit", "words": outside}
    fill = any(word in text for word in _FILL)
    check = any(word in text for word in _CHECK)
    if fill and check:
        return {"kind": "choose"}
    if fill:
        return {"kind": "route", "entry": "cost-modeler-fill"}
    if check:
        return {"kind": "route", "entry": "cost-modeler-validate"}
    return {"kind": "route", "entry": "cost-modeler-help"}


def route(text: str) -> str:
    decision = classify(text)
    if decision["kind"] == "route":
        return decision["entry"]
    return decision["kind"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="根据一句话需求路由至软件成本建模技能族的对应入口")
    parser.add_argument("text", help="用户的原始需求语句")
    args = parser.parse_args(argv)
    decision = classify(args.text)
    if decision["kind"] == "limit":
        words = "、".join(decision["words"])
        print(
            f"这句话里的「{words}」超出本技能族的职责边界。"
            "本入口不删除数据、不安装组件、不直接改写工作簿、不联网，也不调用其他技能。"
            "这次不启动检查或填写。"
        )
        print("如需了解完整能力范围，请调用说明入口 cost-modeler-help。")
        return 2
    if decision["kind"] == "choose":
        print("这句话同时包含检查和填写两类动作。两件事的结果不同，需要你选定一件。")
        print("只读检查工作簿并出具报告，入口是 cost-modeler-validate。")
        print("围绕指定行按现场事实推导并填写空白格，入口是 cost-modeler-fill。")
        print("这次不启动任何一项。请明确其中一项后再运行。")
        return 2
    print(decision["entry"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
