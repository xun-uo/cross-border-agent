# -*- coding: utf-8 -*-
"""验 #43：非物流问题不该被塞物流段；物流问题应该照常给运单号/预计送达。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app import agent  # noqa: E402

LOGISTIC_WORDS = ("运单", "承运商", "YunExpress", "CN2026", "预计送达", "在途", "分拣中心")


def ask(text, history, tag):
    r = agent.process(text, bound_order="ORDER20261021001", force_language="zh",
                      history=history)
    intent = None
    for s in r.get("steps", []):
        if s.get("step") == "intent":
            intent = (s.get("output") or {}).get("intent")
    ans = (r.get("final") or {}).get("text", "")
    hit = [w for w in LOGISTIC_WORDS if w in ans]
    print(f"--- {tag} ---")
    print("问:", text)
    print("意图:", intent, "| 判定:", (r.get("final") or {}).get("verdict"))
    print("答:", ans.replace("\n", " ")[:220])
    print("含物流词:", hit)
    return {"role": "assistant", "content": ans, "language": "zh"}


h = []
h.append({"role": "user", "content": "这个面霜能去黑头吗", "language": "zh"})
h.append(ask("这个面霜能去黑头吗", [], "产品功效（不该有物流）"))
h.append({"role": "user", "content": "那能干嘛", "language": "zh"})
h.append(ask("那能干嘛", h[:2], "追问（不该有物流）"))
h.append({"role": "user", "content": "我的订单在哪", "language": "zh"})
ask("我的订单在哪", h[:4], "物流（应该有运单/预计送达）")
