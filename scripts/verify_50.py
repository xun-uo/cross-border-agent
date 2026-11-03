# -*- coding: utf-8 -*-
"""验 #50：买家写的假订单号不该顶掉登录绑定订单。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app import agent  # noqa: E402

CASES = [
    ("查一下这个包裹的物流信息 ORDER20261028888", "ORDER20261021017", "假号 + 已绑定 → 用绑定那单答"),
    ("ORDER20261028888 这个到哪了", "ORDER20261021017", "假号 + 已绑定 → 用绑定那单答"),
    ("查一下这个包裹的物流信息 ORDER20261028888", None, "假号 + 未绑定 → 固定话术问单号"),
    ("我的订单在哪", "ORDER20261021017", "真号（绑定）→ 正常答"),
]

for text, bound, tag in CASES:
    r = agent.process(text, bound_order=bound, force_language="zh")
    it = [s["output"] for s in r["steps"] if s["step"] == "intent"][0]
    ans = r["final"]["text"]
    tool = [s for s in r["steps"] if s["step"] == "tool"]
    has_order = bool(tool and tool[0].get("order"))
    print("---", tag)
    print("  问:", text)
    print("  工具拿到订单:", has_order, "| 忽略他用号:", it.get("_order_no_ignored"),
          "| 没查到:", it.get("_order_no_not_found"))
    print("  答:", ans.replace("\n", " | ")[:170])
    print("  还在要运单号/订单号:", ("运单号" in ans and bound) or ("请提供" in ans and "订单号" in ans))
