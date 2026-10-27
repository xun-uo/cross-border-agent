# -*- coding: utf-8 -*-
"""跨境智服 Agent · Streamlit 演示界面

启动：
  .venv\\Scripts\\python.exe -m streamlit run web\\app.py --server.port 8501
"""
import json
import os
import sys
from datetime import date
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import agent, compliance  # noqa: E402

# ---------------- 配置 ----------------
def _st_secret(name, default):
    """Streamlit Cloud 的 Secrets 优先于环境变量。"""
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


PASSWORD = str(os.environ.get("DEMO_PASSWORD") or _st_secret("DEMO_PASSWORD", "xinghe2026"))
DAILY_LIMIT = int(os.environ.get("DAILY_LIMIT") or _st_secret("DAILY_LIMIT", 300))
USAGE_FILE = ROOT / "data" / "_usage.json"

st.set_page_config(page_title="跨境智服 Agent", page_icon="🛒", layout="wide")


@st.cache_resource
def _warmup():
    """启动时预热一次，避免第一条消息吃冷启动。"""
    from app import llm
    return llm.warmup()

STEP_ICON = {
    "intent": "①",
    "tool": "②",
    "draft": "③",
    "compliance": "④",
    "action": "⑤",
}
STEP_TITLE = {
    "intent": "意图识别",
    "tool": "工具与检索",
    "draft": "生成草稿",
    "compliance": "合规判定",
    "action": "处置动作",
}


# ---------------- 用量控制 ----------------
def load_usage():
    today = date.today().isoformat()
    try:
        data = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    return data.get(today, 0)


def bump_usage():
    today = date.today().isoformat()
    n = load_usage() + 1
    try:
        USAGE_FILE.write_text(json.dumps({today: n}, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return n


# ---------------- 登录 ----------------
def login_gate():
    if st.session_state.get("authed"):
        return True
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown("## 跨境智服 Agent")
        st.caption("多语言客服 · 合规自检 · 演示环境")
        with st.form("login_form"):
            pwd = st.text_input("访问口令", type="password", placeholder="请输入演示口令")
            ok = st.form_submit_button("进入", use_container_width=True)
        if ok:
            if pwd == PASSWORD:
                st.session_state.authed = True
                st.session_state.history = []
                st.session_state.last_trace = None
                st.rerun()
            else:
                st.error("口令错误")
        st.caption("演示账号由参赛团队提供，仅用于作品体验。")
    return False


# ---------------- trace 面板 ----------------
def render_trace(trace):
    if not trace:
        st.caption("提交一条消息后，这里会显示每一层的输入输出。")
        return

    final = trace.get("final", {})
    verdict = final.get("verdict", "-")
    if verdict == "block":
        st.error(f"判定：拦截（{final.get('level')}）")
    elif verdict == "rewrite":
        st.warning(f"判定：改写（{final.get('level')}）")
    elif verdict == "ask":
        st.info("判定：需要补充信息（追问订单号）")
    else:
        st.success("判定：放行（L3）")

    if final.get("clauses"):
        st.markdown("**命中条款**")
        for c in final["clauses"]:
            st.markdown(f"- {c}")

    st.markdown("**处理链路**")
    for step in trace.get("steps", []):
        name = step["step"]
        with st.expander(f"{STEP_ICON.get(name, '·')} {STEP_TITLE.get(name, name)}　{step['ms']}ms"):
            if name == "intent":
                out = step.get("output", {})
                st.markdown(
                    f"- 主意图：`{out.get('intent')}`\n"
                    f"- 附加标记：`{out.get('flags')}`\n"
                    f"- 情绪：`{out.get('emotion')}`\n"
                    f"- 转人工：`{out.get('need_human')}`\n"
                    f"- 语言：`{out.get('language')}`"
                )
            elif name == "tool":
                order = step.get("order")
                if order:
                    st.markdown(
                        f"- 订单：`{order['order_no']}`　状态：`{order['status_cn']}`\n"
                        f"- 运单：`{order.get('tracking_no') or '—'}`\n"
                        f"- 预计到达：`{order.get('eta_from')} ~ {order.get('eta_to')}`"
                    )
                else:
                    st.markdown(f"- {step.get('note', '无订单')}")
                if step.get("kb"):
                    st.markdown(f"- 检索命中：`{', '.join(step['kb'])}`")
            elif name == "draft":
                st.text(step.get("text", ""))
            elif name == "compliance":
                out = step.get("output", {})
                st.markdown(f"- 结论：`{out.get('verdict')}`　级别：`{out.get('level')}`")
                st.markdown(f"- 原因：{out.get('reason')}")
                for c in out.get("claims", []):
                    flag = "豁免" if c["exempt"] else ("命中" if c["hits"] else "无命中")
                    st.markdown(f"  - [{flag}] {c['text'][:60]}")
            elif name == "action":
                st.text(step.get("text", ""))

    st.caption(
        f"总耗时 {trace.get('ms_total')}ms　"
        f"模型调用 {trace.get('usage', {}).get('calls', 0)} 次"
    )


# ---------------- 主界面 ----------------
def main():
    if not login_gate():
        return

    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_trace" not in st.session_state:
        st.session_state.last_trace = None

    with st.sidebar:
        st.markdown("### 演示控制台")
        used = load_usage()
        st.progress(min(used / DAILY_LIMIT, 1.0), text=f"今日调用 {used} / {DAILY_LIMIT}")

        market_label = st.selectbox("市场", ["自动（按订单）", "US", "EU", "CN"])
        market = None if market_label.startswith("自动") else market_label
        category = st.selectbox("品类", ["cosmetic", "supplement", "medical_device"],
                                format_func=lambda x: {"cosmetic": "化妆品",
                                                       "supplement": "膳食补充剂",
                                                       "medical_device": "医疗器械"}[x])

        st.markdown("**快捷订单**")
        demo_orders = ["ORDER20261021001", "ORDER20261021015", "ORDER20261021007",
                       "ORDER20261021003", "ORDER20261021005"]
        picked = st.selectbox("选一个订单号", ["（不用）"] + demo_orders)
        st.caption("在消息里带上订单号，系统会读取真实状态。")

        st.divider()
        if st.button("清空对话", use_container_width=True):
            st.session_state.history = []
            st.session_state.last_trace = None
            st.rerun()

        st.caption("演示环境，数据为 Mock。\n合规判定不调用模型，秒级返回。")

    st.markdown("### 跨境智服 Agent")
    st.caption("用买家语言回复，并在发出前完成合规判定。左侧提问，右侧看每一层的处理过程。")

    left, right = st.columns([1.6, 1], gap="large")

    with left:
        if not st.session_state.history:
            with st.chat_message("assistant"):
                st.markdown("您好，请在下方输入买家问题。\n\n"
                            "试试：\n"
                            "- `Where is my order?`（会先追问订单号）\n"
                            "- `My order ORDER20261021001 hasn't arrived.`\n"
                            "- `This supplement can cure insomnia and anxiety.`")
        for msg in st.session_state.history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    with right:
        st.markdown("#### 处理链路（trace）")
        render_trace(st.session_state.last_trace)

    placeholder = "输入买家消息，例如 Where is my order?"
    if picked != "（不用）" and not st.session_state.history:
        placeholder = f"输入消息（订单 {picked} 已选）"

    text = st.chat_input(placeholder)
    if not text:
        return

    if used >= DAILY_LIMIT:
        st.session_state.history.append({"role": "user", "content": text})
        st.session_state.history.append({
            "role": "assistant",
            "content": "今日体验额度已用完，请明天再试。如需继续体验可联系参赛团队。",
        })
        st.rerun()

    if picked != "（不用）" and picked not in text and not agent.extract_order_no(text):
        text = f"{text}\n\n（订单号：{picked}）"

    st.session_state.history.append({"role": "user", "content": text})

    with st.spinner("处理中…"):
        try:
            trace = agent.process(text, market=market, category=category)
        except Exception as e:
            st.session_state.history.append({
                "role": "assistant",
                "content": f"处理出错：{type(e).__name__}。请稍后重试。",
            })
            st.rerun()
            return

    st.session_state.history.append({
        "role": "assistant",
        "content": trace["final"]["text"],
    })
    st.session_state.last_trace = trace
    bump_usage()
    st.rerun()


main()
