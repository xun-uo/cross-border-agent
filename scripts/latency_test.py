# -*- coding: utf-8 -*-
"""延迟诊断：拆开单次 API 调用与完整链路的耗时。"""
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import agent, llm  # noqa: E402

out = []


def bench_chat(label, messages, n=3, **kw):
    times = []
    for _ in range(n):
        t = time.perf_counter()
        try:
            llm.chat(messages, **kw)
            times.append((time.perf_counter() - t) * 1000)
        except Exception as e:
            out.append(f"{label}: ERR {e}")
    if times:
        out.append(f"{label}: {[round(x) for x in times]} ms  avg={round(statistics.mean(times))}")
    return times


# 1) 裸调用：最小请求
bench_chat("bare(8 tok)", [{"role": "user", "content": "Reply with: OK"}], n=3, max_tokens=8)

# 2) 意图识别
bench_chat("intent", [{"role": "system", "content": agent.INTENT_SYS},
                      {"role": "user", "content": "Where is my order?"}],
           n=3, max_tokens=300)

# 3) 完整链路
out.append("")
for i in range(3):
    t = time.perf_counter()
    trace = agent.process("My order ORDER20261021001 hasn't arrived. Where is it?")
    total = (time.perf_counter() - t) * 1000
    steps = ", ".join(f"{s['step']}={s['ms']}" for s in trace["steps"])
    out.append(f"pipeline#{i+1}: total={round(total)}ms  [{steps}]")

# 4) 纯本地部分（合规判定，无模型）
t = time.perf_counter()
for _ in range(10):
    agent.compliance.evaluate("This supplement can cure insomnia and anxiety.", "US", "supplement")
out.append(f"\ncompliance.evaluate x10: {round((time.perf_counter()-t)*1000)}ms 总计（单次约 {round((time.perf_counter()-t)*100)}ms）")

open(ROOT / "out" / "latency.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
