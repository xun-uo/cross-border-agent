# -*- coding: utf-8 -*-
"""验证：调用次数是否降到 2-3 次；登录是否改成账号+密码。"""
import sys

sys.path.insert(0, r"D:\跨境智服")

out = []

# 1) 调用次数
from app import agent  # noqa: E402
before = dict(agent.llm._last_usage)
trace = agent.process("My order ORDER20261021001 hasn't arrived. Where is it?")
after = agent.llm._last_usage
out.append(f"calls_delta={after['calls'] - before['calls']}  "
           f"prompt={after['prompt_tokens'] - before['prompt_tokens']}  "
           f"total_ms={trace['ms_total']}")
out.append(f"verdict={trace['final']['verdict']}")

# 2) UI 登录表单
from streamlit.testing.v1 import AppTest  # noqa: E402

at = AppTest.from_file(r"D:\跨境智服\web\app.py", default_timeout=120)
at.run()
labels = [t.label for t in at.text_input]
out.append(f"login_fields={labels}")
out.append(f"buttons={[b.label for b in at.button]}")

# 3) 用正确账号密码登录后应进入主界面
at2 = AppTest.from_file(r"D:\跨境智服\web\app.py", default_timeout=120)
at2.session_state["authed"] = True
at2.session_state["history"] = []
at2.session_state["last_trace"] = None
at2.run()
out.append(f"authed_chat_input={len(at2.chat_input)}  selectbox={len(at2.selectbox)}")

open(r"D:\跨境智服\out\verify_fix.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
