# -*- coding: utf-8 -*-
"""验 #48：超长多主题输入必定转人工；短的政策问题仍由 AI 直答。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app import agent  # noqa: E402

txt = io.open(r"D:\跨境智服\out\超长输入-8000字.txt", encoding="utf-8").read()
print("长文本长度:", len(txt))

for i in range(2):
    r = agent.process(txt, bound_order="ORDER20261021017", force_language="zh")
    it = [s["output"] for s in r["steps"] if s["step"] == "intent"][0]
    ans = r["final"]["text"]
    print("  第%d次: 意图=%s need_human=%s handoff=%s 答里有同事提示=%s 答长=%d"
          % (i + 1, it.get("intent"), it.get("need_human"),
             r["final"].get("handoff"), "同事" in ans, len(ans)))

for q in ["退货政策是什么", "无理由退货是几天", "能退吗"]:
    r = agent.process(q, bound_order="ORDER20261021017", force_language="zh")
    print("  「%s」→ handoff=%s" % (q, r["final"].get("handoff")))
