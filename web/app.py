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
from PIL import Image, ImageDraw, ImageFont

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


ACCOUNT = str(os.environ.get("DEMO_ACCOUNT") or _st_secret("DEMO_ACCOUNT", "judge"))
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
    "semantic": "④b",
    "action": "⑤",
}
STEP_TITLE = {
    "intent": "意图识别",
    "tool": "工具与检索",
    "draft": "生成草稿",
    "compliance": "合规判定",
    "semantic": "语义复核",
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
            acct = st.text_input("账号", placeholder="演示账号")
            pwd = st.text_input("密码", type="password", placeholder="演示密码")
            ok = st.form_submit_button("进入", use_container_width=True)
        if ok:
            if acct.strip().lower() == ACCOUNT.lower() and pwd == PASSWORD:
                st.session_state.authed = True
                st.session_state.history = []
                st.session_state.last_trace = None
                st.rerun()
            else:
                st.error("账号或密码错误")
        st.caption("演示账号请使用参赛团队提供的凭证。")
        st.caption("首次打开需要唤醒实例，约 30–60 秒；唤醒后访问很快，请耐心等待。")
    return False


# ---------------- trace 面板 ----------------
BUILD = "2026-10-29 #20 · dark-switch"  # 改代码时顺手改这里，用来确认线上是否已生效


def _load_font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              r"C:\Windows\Fonts\arial.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def _route_image(nodes, order_no="", width=1000, height=150):
    """物流路线示意图：本地渲染，不依赖地图底图与网络。"""
    bg, line_c = (24, 34, 50, 255), (70, 110, 160, 255)
    dot, dot_now = (66, 133, 244, 255), (56, 200, 120, 255)
    dim, txt = (140, 155, 175, 255), (225, 232, 245, 255)

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, width - 1, height - 1], radius=14, fill=bg)

    f_title, f_small, f_big = _load_font(15), _load_font(12), _load_font(14)
    d.text((24, 14), f"Route · {order_no}" if order_no else "Route", font=f_title, fill=txt)

    n = len(nodes)
    x0, x1 = 74, width - 74
    y = 86
    step = (x1 - x0) / (n - 1) if n > 1 else 0
    d.line([(x0, y), (x1, y)], fill=line_c, width=3)

    for i, node in enumerate(nodes):
        x = x0 + step * i
        last = i == n - 1
        if last:
            d.ellipse([x - 17, y - 17, x + 17, y + 17], outline=(56, 200, 120, 110), width=2)
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=dot_now)
        else:
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=dot)
        d.text((x, y - 30), str(i + 1), font=f_small, fill=dim, anchor="ma")
        t = node["time"][5:16] if len(node["time"]) >= 16 else node["time"]
        d.text((x, y + 18), t, font=f_small, fill=dot_now if last else dim, anchor="ma")

    d.text((x0, y + 40), "ORIGIN", font=f_big, fill=dim, anchor="ma")
    d.text((x1, y + 40), "NOW", font=f_big, fill=dot_now, anchor="ma")
    return img


def _haversine_km(a, b):
    import math
    lat1, lon1, lat2, lon2 = map(math.radians, (a["lat"], a["lng"], b["lat"], b["lng"]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def _great_circle(lat1, lon1, lat2, lon2, n=64):
    """大圆航线插值：跨洋段按真实航班走向铺点，而不是投影直线。"""
    import math
    p1, l1, p2, l2 = map(math.radians, (lat1, lon1, lat2, lon2))
    d = 2 * math.asin(math.sqrt(
        math.sin((p2 - p1) / 2) ** 2 +
        math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2))
    if d < 1e-9:
        return [[lon1, lat1], [lon2, lat2]]
    out = []
    for i in range(n + 1):
        f = i / n
        A = math.sin((1 - f) * d) / math.sin(d)
        B = math.sin(f * d) / math.sin(d)
        x = A * math.cos(p1) * math.cos(l1) + B * math.cos(p2) * math.cos(l2)
        y = A * math.cos(p1) * math.sin(l1) + B * math.cos(p2) * math.sin(l2)
        z = A * math.sin(p1) + B * math.sin(p2)
        out.append([math.degrees(math.atan2(y, x)),
                    math.degrees(math.atan2(z, math.sqrt(x * x + y * y)))])
    return out


def _build_track(pts):
    """相邻节点连线；超过 2000km 的段改用大圆航线。"""
    path = []
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if _haversine_km(a, b) > 2000:
            seg = _great_circle(a["lat"], a["lng"], b["lat"], b["lng"])
            path.extend(seg if not path else seg[1:])
        else:
            if not path:
                path.append([float(a["lng"]), float(a["lat"])])
            path.append([float(b["lng"]), float(b["lat"])])
    return path


def _map_deck(nodes, order_no=""):
    """真地图：有经纬度就用 pydeck 画轨迹，否则返回 None 交给路线图兜底。"""
    pts = [n for n in nodes if "lat" in n and "lng" in n]
    if len(pts) < 2:
        return None
    try:
        import pydeck as pdk
    except Exception:
        return None

    path = _build_track(pts)
    last = pts[-1]

    # 跨洋段用 ArcLayer：弧线在屏幕上会明显拱起，视觉上就是“飞过去”的轨迹
    arc_layer = pdk.Layer(
        "ArcLayer",
        data=[{
            "from": [float(pts[0]["lng"]), float(pts[0]["lat"])],
            "to": [float(last["lng"]), float(last["lat"])],
        }],
        get_source_position="from",
        get_target_position="to",
        get_source_color=[66, 133, 244],
        get_target_color=[56, 200, 120],
        get_width=3,
        get_height=1.2,
        great_circle=True,
    )
    path_layer = pdk.Layer(
        "PathLayer",
        data=[{"path": path}],
        get_path="path",
        get_color=[120, 170, 230, 120],
        width_min_pixels=2,
        get_width=3,
    )
    stop_layer = pdk.Layer(
        "ScatterplotLayer",
        data=[{"lng": float(n["lng"]), "lat": float(n["lat"]), "desc": n["desc"]} for n in pts[:-1]],
        get_position=["lng", "lat"],
        get_color=[66, 133, 244],
        get_radius=45000,
        pickable=True,
    )
    now_layer = pdk.Layer(
        "ScatterplotLayer",
        data=[{"lng": float(last["lng"]), "lat": float(last["lat"]), "desc": last["desc"]}],
        get_position=["lng", "lat"],
        get_color=[56, 200, 120],
        get_radius=70000,
        pickable=True,
    )
    # 中心放在太平洋、zoom 2.2：整条弧线能完整入镜，又不会平铺出多份世界
    view = pdk.ViewState(
        latitude=46,
        longitude=-170,
        zoom=2.2,
        pitch=0,
    )
    return pdk.Deck(
        layers=[path_layer, stop_layer, now_layer],
        initial_view_state=view,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={"text": "{desc}"},
    )


def _timeline_md(nodes):
    """物流轨迹：markdown 列表，每项一行。"""
    lines = []
    last = len(nodes) - 1
    for i, n in enumerate(nodes):
        dot = "🟢" if i == last else "🔵"
        bold = "**" if i == last else ""
        lines.append(f"- {dot} `{n['time']}`　{bold}{n['desc']}{bold}")
    return "\n".join(lines)


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
                    if order.get("nodes"):
                        st.markdown("**物流路线**")
                        try:
                            st.image(_route_image(order["nodes"], order["order_no"]),
                                     use_container_width=True)
                        except Exception:
                            pass
                        with st.expander("轨迹明细"):
                            st.markdown(_timeline_md(order["nodes"]))
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
            elif name == "semantic":
                out = step.get("output", {}) or {}
                st.markdown(
                    f"- 结论：`{out.get('verdict')}`　级别：`{out.get('level')}`\n"
                    f"- 原因：{out.get('reason')}")
            elif name == "action":
                st.text(step.get("text", ""))

    st.caption(
        f"总耗时 {trace.get('ms_total')}ms　"
        f"模型调用 {trace.get('usage', {}).get('calls', 0)} 次"
    )


# ---------------- 主界面 ----------------

# ---------------- 样式：买家消息右对齐 ----------------
CHAT_CSS = """
<style>
/* 两边都画气泡：外层去底色，内容层收缩并加圆角 */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    align-items: flex-start;
}
[data-testid="stChatMessage"] > div:not([data-testid^="stChatMessageAvatar"]) {
    flex: 0 1 auto;
    max-width: 78%;
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,.28);
    border-radius: 14px;
    padding: 10px 18px;
    box-shadow: 0 2px 8px rgba(0,0,0,.08);
}
/* 买家：反向排列 + 靠右 + 淡金边 */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) > div:not([data-testid^="stChatMessageAvatar"]) {
    margin-left: auto;
    margin-right: 10px;
    text-align: right;
    border-color: rgba(201,168,130,.45);
    background: rgba(201,168,130,.13);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"],
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stCaptionContainer"] {
    text-align: right;
}
/* 客服：靠左 */
[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageAvatarUser"])) > div:not([data-testid^="stChatMessageAvatar"]) {
    margin-right: auto;
    margin-left: 10px;
    text-align: left;
}
</style>
"""

# ---------------- 品牌栏 ----------------
STORE_NAME = "Niao Store"


DARK_CSS = """
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background: #0E1117 !important;
}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 {
    color: #E6E2DA !important;
}
[data-testid="stCaptionContainer"] p { color: #8C8478 !important; }
[data-testid="stChatMessage"] > div:not([data-testid^="stChatMessageAvatar"]) {
    background: #1E1E1B !important;
    border-color: rgba(255,255,255,.10) !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) > div:not([data-testid^="stChatMessageAvatar"]) {
    background: rgba(201,168,130,.14) !important;
    border-color: rgba(201,168,130,.45) !important;
}
[data-testid="stChatInput"] { background: #16161A !important; }
[data-testid="stChatInput"] textarea { color: #E6E2DA !important; }
[data-testid="stBottom"] > div { background: #0E1117 !important; }
[data-testid="stButton"] button {
    background: transparent !important; color: #D8D3C8 !important;
    border-color: rgba(255,255,255,.16) !important;
}
</style>
"""


def render_brand():
    c1, c2, c3 = st.columns([4, 1.5, 0.9])
    with c1:
        st.markdown(f"#### 🏪 {STORE_NAME}")
        st.caption("● 在线 · 通常几秒内回复 · 中 / 英 / 西")
    with c2:
        show_debug = st.toggle("显示处理过程", value=False,
                               help="答辩演示用：展开每一层的判定结果与调试参数")
    with c3:
        st.toggle("深色", value=False, key="dark_bg", help="切换背景深浅")
    return show_debug


def render_quick_pills():
    quick = ["Where is my order?", "Return policy", "Product info"]
    cols = st.columns(len(quick))
    for c, q in zip(cols, quick):
        if c.button(q, use_container_width=True, key=f"quick_{q}"):
            st.session_state["pending"] = q
            st.rerun()


def render_debug_panel():
    st.markdown("##### 处理过程")
    render_trace(st.session_state.last_trace)

    st.divider()
    st.markdown("##### 调试参数")
    used = load_usage()
    st.progress(min(used / DAILY_LIMIT, 1.0), text=f"今日调用 {used} / {DAILY_LIMIT}")

    labels = ["自动（按订单/原文）", "US", "EU", "CN"]
    cur = st.session_state.get("dbg_market", labels[0])
    market_label = st.selectbox("市场", labels, index=labels.index(cur) if cur in labels else 0)
    st.session_state["dbg_market"] = market_label

    cats = ["cosmetic", "supplement", "medical_device"]
    cur_cat = st.session_state.get("dbg_category", "cosmetic")
    category = st.selectbox("品类兜底", cats,
                            index=cats.index(cur_cat) if cur_cat in cats else 0,
                            format_func=lambda x: {"cosmetic": "化妆品",
                                                   "supplement": "膳食补充剂",
                                                   "medical_device": "医疗器械"}[x],
                            help="仅在订单与买家原话都推断不出品类时使用")
    st.session_state["dbg_category"] = category

    demo_orders = ["（不用）", "ORDER20261021001", "ORDER20261021015",
                   "ORDER20261021007", "ORDER20261021003", "ORDER20261021005"]
    cur_o = st.session_state.get("dbg_order", "（不用）")
    picked = st.selectbox("快捷订单", demo_orders,
                          index=demo_orders.index(cur_o) if cur_o in demo_orders else 0)
    st.session_state["dbg_order"] = picked

    st.divider()
    if st.button("清空对话", use_container_width=True):
        st.session_state.history = []
        st.session_state.last_trace = None
        st.rerun()

    st.caption("演示环境，数据为 Mock。合规判定不调用模型。")
    st.caption(f"build {BUILD}")


def _now():
    import datetime
    return datetime.datetime.now().strftime("%H:%M")


def _run_turn(text):
    """执行一轮问答并写回历史。"""
    market_label = st.session_state.get("dbg_market", "自动（按订单/原文）")
    market = None if market_label.startswith("自动") else market_label
    category = st.session_state.get("dbg_category", "cosmetic")
    picked = st.session_state.get("dbg_order", "（不用）")

    if picked != "（不用）" and picked not in text and not agent.extract_order_no(text):
        text = f"{text}\n\n（订单号：{picked}）"

    st.session_state.history.append({"role": "user", "content": text, "ts": _now()})
    with st.chat_message("user"):
        st.markdown(text)
    status = st.empty()
    status.caption("正在处理…")

    with st.spinner("处理中…"):
        try:
            trace = agent.process(text, market=market, category=category)
        except Exception as e:
            st.session_state.history.append({
                "role": "assistant",
                "content": f"抱歉，处理出错了（{type(e).__name__}），请稍后重试。",
                "ts": _now(),
            })
            st.rerun()
            return

    st.session_state.history.append({
        "role": "assistant",
        "content": trace["final"]["text"],
        "ts": _now(),
    })
    st.session_state.last_trace = trace
    bump_usage()
    status.empty()
    st.rerun()


def main():
    if not login_gate():
        return

    st.session_state.setdefault("history", [])
    st.session_state.setdefault("last_trace", None)
    st.session_state.setdefault("dbg_market", "自动（按订单/原文）")
    st.session_state.setdefault("dbg_category", "cosmetic")
    st.session_state.setdefault("dbg_order", "（不用）")

    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    if st.session_state.get("dark_bg"):
        st.markdown(DARK_CSS, unsafe_allow_html=True)
    show_debug = render_brand()

    if show_debug:
        chat_col, side = st.columns([1.55, 1], gap="large")
    else:
        chat_col, side = st.container(), None

    with chat_col:
        if not st.session_state.history:
            with st.chat_message("assistant"):
                st.markdown("Hi! 我是这家店的客服助手。物流、退换货、产品问题都可以问我。")
            render_quick_pills()
        for msg in st.session_state.history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("ts"):
                    st.caption(msg["ts"])

    if side is not None:
        with side:
            render_debug_panel()

    # 快捷问题触发
    if st.session_state.get("pending"):
        text = st.session_state.pop("pending")
        _run_turn(text)
        return

    # 额度检查
    used = load_usage()
    if used >= DAILY_LIMIT:
        st.caption("今日体验额度已用完，请明天再试。")
        return

    placeholder = "输入你的问题，例如 Where is my order?"
    text = st.chat_input(placeholder)
    if text:
        _run_turn(text)


main()
