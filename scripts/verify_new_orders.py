# -*- coding: utf-8 -*-
"""验新增的五个市场订单能否被查到并走完整问答。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\跨境智服")

from app import agent  # noqa: E402

CASES = [
    ("ORDER20261021021", "0021", "PH"),
    ("ORDER20261021022", "0022", "PH"),
    ("ORDER20261021023", "0023", "KR"),
    ("ORDER20261021025", "0025", "RU"),
    ("ORDER20261021027", "0027", "MN"),
    ("ORDER20261021029", "0029", "CN"),
    ("ORDER20261021030", "0030", "CN"),
]

print("=== 订单能否查到 ===")
for no, tail, mk in CASES:
    o = agent.find_order(no)
    if not o:
        print("  %s  ❌ 查不到" % no)
        continue
    ok_tail = (o.get("phone") or "")[-4:] == tail
    print("  %s  %-3s %-18s %-10s 节点%d  尾号%s"
          % (no, o["market"], o["customer"], o["status_cn"],
             len(o.get("nodes") or []), "✓" if ok_tail else "❌" + (o.get("phone") or "")[-4:]))

print("\n=== 完整问答（走真实模型） ===")
for no, mk in (("ORDER20261021021", "PH"), ("ORDER20261021025", "RU"), ("ORDER20261021029", "CN")):
    lang = "zh" if mk == "CN" else "en"
    try:
        tr = agent.process("我的订单到哪了", force_language=lang, bound_order=no)
        f = tr["final"]
        print("  %s | market=%s verdict=%s lang=%s"
              % (no, f.get("market"), f.get("verdict"), f.get("language")))
        print("     " + (f.get("text") or "")[:110].replace("\n", " "))
    except Exception as e:
        print("  %s  ERROR %s: %s" % (no, type(e).__name__, e))
