# -*- coding: utf-8 -*-
"""用 Streamlit 的 AppTest 验证界面逻辑（不需要浏览器）。"""
import sys

sys.path.insert(0, r"D:\跨境智服")

from streamlit.testing.v1 import AppTest

APP = r"D:\跨境智服\web\app.py"
out = []

# 1) 未登录：应停在登录页
at = AppTest.from_file(APP, default_timeout=120)
at.run()
out.append(f"[未登录] exception={at.exception}")
out.append(f"  text_input 数量={len(at.text_input)}  button 数量={len(at.button)}")

# 2) 已登录：应渲染主界面
at2 = AppTest.from_file(APP, default_timeout=120)
at2.session_state["authed"] = True
at2.session_state["history"] = []
at2.session_state["last_trace"] = None
at2.run()
out.append(f"[已登录] exception={at2.exception}")
out.append(f"  chat_input 数量={len(at2.chat_input)}  selectbox 数量={len(at2.selectbox)}")
out.append(f"  columns/标题: {[m.value for m in at2.markdown][:4]}")

open(r"D:\跨境智服\out\ui_test.txt", "w", encoding="utf-8").write("\n".join(out))
print("\n".join(out))
