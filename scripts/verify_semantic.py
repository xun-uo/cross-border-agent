# -*- coding: utf-8 -*-
"""验证语义层接入后的完整链路与延迟。"""
import sys
import time

sys.path.insert(0, r"D:\跨境智服")
from app import agent  # noqa: E402

cases = [
    ("物流类（不应触发语义层）", "My order ORDER20261021001 hasn't arrived.", 0),
    ("产品咨询（会触发语义层）", "Is this cream suitable for sensitive skin?", 0),
    ("产品咨询+违规草稿风险", "Does this supplement help with sleep?", 0),
]
lines = []
for label, q, _ in cases:
    t0 = time.perf_counter()
    tr = agent.process(q)
    ms = (time.perf_counter() - t0) * 1000
    steps = [s["step"] for s in tr["steps"]]
    lines.append(f"{label}")
    lines.append(f"  intent={tr['steps'][0]['output'].get('intent')}  steps={steps}")
    lines.append(f"  verdict={tr['final']['verdict']}  calls={tr['usage']['calls']}  total={round(ms)}ms")
    lines.append(f"  reply={tr['final']['text'][:90].replace(chr(10),' ')}")
    lines.append("")

out = "\n".join(lines)
open(r"D:\跨境智服\out\semantic_pipeline.txt", "w", encoding="utf-8").write(out)
print(out)
