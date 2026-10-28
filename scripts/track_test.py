# -*- coding: utf-8 -*-
"""测试：买家问物流轨迹/路线时，Agent 能否给出节点序列。"""
import sys

sys.path.insert(0, r"D:\跨境智服")
from app import agent  # noqa: E402

cases = [
    "Can you show me the tracking history of my order? ORDER20261021001",
    "Where exactly is my package now? ORDER20261021001",
    "走的什么路线？到哪了？ORDER20261021001",
]

lines = []
for q in cases:
    t = agent.process(q)
    lines.append("=" * 60)
    lines.append(f"Q: {q}")
    lines.append(f"intent={t['steps'][0]['output'].get('intent')}  verdict={t['final']['verdict']}")
    lines.append("A: " + t["final"]["text"].replace("\n", " "))
    lines.append("")

open(r"D:\跨境智服\out\track_test.txt", "w", encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
