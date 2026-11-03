# -*- coding: utf-8 -*-
"""最小复现：切下拉框后如何把参数写进地址栏（四种写法对比）。

对应待修清单 #38：切语言后 URL 的 l= 参数不更新。
模式用 URL 指定：?mode=A|B|C|D
运行：.venv\\Scripts\\python.exe -m streamlit run scripts\\probe_qp_app.py --server.port 8511 --server.headless=true
"""
import streamlit as st

st.set_page_config(page_title="qp probe", layout="wide")

mode = (st.query_params.get("mode") or "A").upper()[:1]
OPTS = ["zh", "th", "en"]
CUR = st.session_state.get("ui_lang") or st.query_params.get("l") or "zh"
if CUR not in OPTS:
    CUR = "zh"

st.write("mode:", mode, "| URL now:", dict(st.query_params), "| ui_lang:", CUR)

if mode == "A":
    # 现状写法：set 完马上 st.rerun()
    pick = st.selectbox("lang A", OPTS, index=OPTS.index(CUR), key="a_pick")
    if pick != CUR:
        st.session_state["ui_lang"] = pick
        st.query_params["l"] = pick
        st.rerun()

elif mode == "B":
    # 回调里写，脚本照常跑完
    def _cb():
        st.session_state["ui_lang"] = st.session_state["b_pick"]
        st.query_params["l"] = st.session_state["b_pick"]

    st.selectbox("lang B", OPTS, index=OPTS.index(CUR), key="b_pick", on_change=_cb)

elif mode == "C":
    # 两阶段：先 rerun，下一轮开头再写
    if st.session_state.pop("_pending_l", None):
        st.query_params["l"] = st.session_state.get("ui_lang", "zh")

    def _cb3():
        st.session_state["ui_lang"] = st.session_state["c_pick"]
        st.session_state["_pending_l"] = True

    st.selectbox("lang C", OPTS, index=OPTS.index(CUR), key="c_pick", on_change=_cb3)

else:
    # 分叉版 Streamlit 的 bind 特性
    pick = st.selectbox("lang D", OPTS, index=OPTS.index(CUR), key="l", bind="query-params")
    if pick != CUR:
        st.session_state["ui_lang"] = pick
