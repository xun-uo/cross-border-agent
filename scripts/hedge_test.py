# -*- coding: utf-8 -*-
"""对冲请求效果测试：连跑 6 次，看延迟分布与调用数。"""
import statistics
import sys
import time

sys.path.insert(0, r"D:\跨境智服")
from app import agent, llm  # noqa: E402

times, calls = [], []
for i in range(6):
    before = llm.usage_snapshot()["calls"]
    t0 = time.perf_counter()
    tr = agent.process("My order ORDER20261021001 hasn't arrived. Where is it?")
    ms = (time.perf_counter() - t0) * 1000
    times.append(ms)
    calls.append(llm.usage_snapshot()["calls"] - before)
    print(f"  run{i+1}: {round(ms)}ms  calls={calls[-1]}")

out = (f"延迟: {[round(t) for t in times]}ms\n"
       f"均值 {round(statistics.mean(times))}ms  中位 {round(statistics.median(times))}ms  "
       f"最大 {round(max(times))}ms\n"
       f"调用数: {calls}  平均 {statistics.mean(calls):.1f}\n")
open(r"D:\跨境智服\out\hedge_test.txt", "w", encoding="utf-8").write(out)
print(out)
