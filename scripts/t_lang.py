# -*- coding: utf-8 -*-
"""直接调 agent，验 force_language 到底管不管用。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\跨境智服")

from app import agent  # noqa: E402

for lang in ("th", "th", "th", "th"):
    try:
        tr = agent.process("我的订单到哪了", force_language=lang,
                           bound_order="ORDER20261021001")
        f = tr["final"]
        print("=" * 12, lang, "| returned:", f.get("language"))
        print(f.get("text", "")[:220])
    except Exception as e:
        print("=" * 12, lang, "ERROR:", type(e).__name__, e)
