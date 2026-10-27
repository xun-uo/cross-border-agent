# -*- coding: utf-8 -*-
"""模拟一次真实提问，验证界面端到端可用。"""
import sys

sys.path.insert(0, r"D:\跨境智服")

from streamlit.testing.v1 import AppTest

APP = r"D:\跨境智服\web\app.py"
out = []

at = AppTest.from_file(APP, default_timeout=180)
at.session_state["authed"] = True
at.session_state["history"] = []
at.session_state["last_trace"] = None
at.run()

at.chat_input[0].set_value("My order ORDER20261021001 hasn't arrived. Where is it?").run()

hist = at.session_state["history"]
out.append(f"exception={at.exception}")
out.append(f"history_len={len(hist)}")
for m in hist:
    out.append(f"[{m['role']}] {m['content'][:300]}")

trace = at.session_state.get("last_trace")
if trace:
    out.append(f"trace steps={[s['step'] for s in trace['steps']]}")
    out.append(f"final verdict={trace['final']['verdict']} ms={trace.get('ms_total')}")
else:
    out.append("trace=None")

open(r"D:\跨境智服\out\ui_chat_test.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
