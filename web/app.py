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

# 账号 -> (密码, 角色)。商家进后台，买家进客服窗口。
ACCOUNTS = {
    "admin":   ("niao2026", "merchant"),
    "judge":   (PASSWORD, "merchant"),
    "buyer":   ("niao2026", "buyer"),
}
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


# ---------------- 界面文案（i18n） ----------------
TEXTS = {
    "zh": {
        "badge": "AI AGENT · 2026",
        "title": "跨境智能客服",
        "sub": "跨境电商客服系统 · 多语言 · 合规自检",
        "account": "账号",
        "password": "密码",
        "login": "进入",
        "wrong": "账号或密码错误",
        "acct_ph": "邮箱或工号",
        "pwd_ph": "请输入密码",
        "cred_hint": "忘记密码请联系店铺管理员。",
        "wake_hint": "服务空闲时会自动休眠，首次访问请稍候。",
        "online": "🟢 在线",
        "welcome": "你好，我是这家店的客服助手。物流、退换货、产品问题都可以问我。",
        "lang_hint": "支持中文 / English / Español —— 直接用你的语言提问，我会用同一种语言回复。",
        "q1": "我的订单在哪？",
        "q2": "退货政策",
        "q3": "产品咨询",
        "placeholder": "输入你的问题，例如：我的订单到哪了？",
        "debug": "显示处理过程",
        "debug_help": "答辩演示用：展开每一层的判定结果与调试参数",
        "processing": "正在处理…",
        "quota": "今日体验额度已用完，请明天再试。",
        "err": "抱歉，处理出错了，请稍后重试。",
        "clear": "清空对话",
        "trace": "处理过程",
        "params": "调试参数",
        "market": "市场",
        "category": "品类兜底",
        "order": "快捷订单",
        "auto": "自动（按订单/原文）",
        "none": "（不用）",
        "usage": "今日调用",
        "login_tab": "登录",
        "signup_tab": "注册",
        "email": "邮箱",
        "email_ph": "you@example.com",
        "pwd_new": "设置密码",
        "pwd_confirm": "确认密码",
        "signup_btn": "创建账号",
        "signup_ok": "注册成功，请用该邮箱登录。",
        "err_email": "请输入有效的邮箱地址。",
        "err_pwd": "两次输入的密码不一致。",
        "err_exists": "该邮箱已注册，请直接登录。",
        "err_short": "密码至少 6 位。",
    },
    "en": {
        "badge": "AI AGENT · 2026",
        "title": "Cross-border Smart Support",
        "sub": "Cross-border support platform · Multilingual · Compliance built in",
        "account": "Account",
        "password": "Password",
        "login": "Sign in",
        "wrong": "Incorrect account or password",
        "acct_ph": "Email or staff ID",
        "pwd_ph": "Enter password",
        "cred_hint": "Forgot password? Contact your store admin.",
        "wake_hint": "The service sleeps when idle; first visit may take a moment.",
        "online": "🟢 Online",
        "welcome": "Hi! I'm this store's support assistant. Ask me about shipping, returns, or products.",
        "lang_hint": "Chinese / English / Español — just ask in your language, I reply in the same one.",
        "q1": "Where is my order?",
        "q2": "Return policy",
        "q3": "Product info",
        "placeholder": "Ask anything, e.g. Where is my order?",
        "debug": "Show trace",
        "debug_help": "For demo: expand every judgement layer and debug params",
        "processing": "Working…",
        "quota": "Daily quota reached. Please try again tomorrow.",
        "err": "Sorry, something went wrong. Please retry.",
        "clear": "Clear chat",
        "trace": "Trace",
        "params": "Debug params",
        "market": "Market",
        "category": "Category fallback",
        "order": "Quick order",
        "auto": "Auto (from order / text)",
        "none": "(none)",
        "usage": "Calls today",
        "login_tab": "Sign in",
        "signup_tab": "Sign up",
        "email": "Email",
        "email_ph": "you@example.com",
        "pwd_new": "Create password",
        "pwd_confirm": "Confirm password",
        "signup_btn": "Create account",
        "signup_ok": "Account created. Please sign in with that email.",
        "err_email": "Please enter a valid email address.",
        "err_pwd": "Passwords do not match.",
        "err_exists": "This email is already registered, please sign in.",
        "err_short": "Password must be at least 6 characters.",
    },
    "es": {
        "badge": "AI AGENT · 2026",
        "title": "Atención Inteligente Transfronteriza",
        "sub": "Plataforma de atención transfronteriza · Multilingüe · Cumplimiento",
        "account": "Cuenta",
        "password": "Contraseña",
        "login": "Entrar",
        "wrong": "Cuenta o contraseña incorrecta",
        "acct_ph": "Correo o ID",
        "pwd_ph": "Introduzca la contraseña",
        "cred_hint": "¿Olvidó su contraseña? Contacte al administrador.",
        "wake_hint": "El servicio se suspende por inactividad; la primera visita puede tardar.",
        "online": "🟢 En línea",
        "welcome": "¡Hola! Soy el asistente de esta tienda. Pregúntame por envíos, devoluciones o productos.",
        "lang_hint": "中文 / English / Español — pregunta en tu idioma y responderé en el mismo.",
        "q1": "¿Dónde está mi pedido?",
        "q2": "Política de devoluciones",
        "q3": "Información del producto",
        "placeholder": "Escribe tu pregunta, ej. ¿Dónde está mi pedido?",
        "debug": "Mostrar traza",
        "debug_help": "Para demo: muestra cada capa del juicio y los parámetros",
        "processing": "Procesando…",
        "quota": "Cuota diaria agotada. Inténtalo mañana.",
        "err": "Lo siento, ocurrió un error. Reintenta.",
        "clear": "Limpiar chat",
        "trace": "Traza",
        "params": "Parámetros",
        "market": "Mercado",
        "category": "Categoría por defecto",
        "order": "Pedido rápido",
        "auto": "Auto (según pedido / texto)",
        "none": "(ninguno)",
        "usage": "Llamadas hoy",
        "login_tab": "Iniciar sesión",
        "signup_tab": "Registrarse",
        "email": "Correo",
        "email_ph": "tu@ejemplo.com",
        "pwd_new": "Crear contraseña",
        "pwd_confirm": "Confirmar contraseña",
        "signup_btn": "Crear cuenta",
        "signup_ok": "Cuenta creada. Inicie sesión con ese correo.",
        "err_email": "Introduzca un correo válido.",
        "err_pwd": "Las contraseñas no coinciden.",
        "err_exists": "Este correo ya está registrado, inicie sesión.",
        "err_short": "La contraseña debe tener al menos 6 caracteres.",
    },
}

LANG_LABELS = {"中文": "zh", "English": "en", "Español": "es"}
DISPLAY_LANG_LABEL = "Language / 语言 / Idioma"


def t(key):
    lang = st.session_state.get("ui_lang", "zh")
    return TEXTS.get(lang, TEXTS["zh"]).get(key, key)


def lang_picker():
    """齿轮 + 下拉：平时只显示当前语言，点开才列出其他。"""
    cur = st.session_state.get("ui_lang", "zh")
    names = list(LANG_LABELS.keys())
    cur_name = next((n for n, v in LANG_LABELS.items() if v == cur), names[0])
    pick = st.selectbox(DISPLAY_LANG_LABEL, names, index=names.index(cur_name),
                        label_visibility="collapsed", key="lang_pick")
    picked = LANG_LABELS[pick]
    if st.session_state.get("ui_lang") != picked:
        st.session_state["ui_lang"] = picked
        st.rerun()   # 立刻重绘，避免顶部文案还是旧语言


def gear(key_suffix=""):
    """右上角语言下拉：平时只显示当前语言，点开才列其他。"""
    lang_picker()


# ---------------- 登录 ----------------
def login_gate():
    if st.session_state.get("authed"):
        return True
    st.session_state.setdefault("ui_lang", "zh")
    st.markdown(FLOAT_CSS, unsafe_allow_html=True)
    st.markdown(FLOATING_STATUS_CSS, unsafe_allow_html=True)

    _, gear_col = st.columns([8, 2])
    with gear_col:
        with st.container(key="lang_box_login"):
            lang_picker()

    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(f"## {t('title')}")
        st.caption(t("sub"))
        with st.form("login_form"):
            acct = st.text_input(t("account"), placeholder=t("acct_ph"))
            pwd = st.text_input(t("password"), type="password", placeholder=t("pwd_ph"))
            ok = st.form_submit_button(t("login"), use_container_width=True)
        if ok:
            key = acct.strip().lower()
            rec = ACCOUNTS.get(key)
            if rec and rec[0] == pwd:
                st.session_state.authed = True
                st.session_state.user = key
                st.session_state.role = rec[1]
                st.session_state.history = []
                st.session_state.last_trace = None
                st.rerun()
            else:
                st.error(t("wrong"))
        st.caption(t("cred_hint"))
        st.caption(t("wake_hint"))
    return False


# ---------------- trace 面板 ----------------
BUILD = "2026-10-31 #73 · human-mode"  # 改代码时顺手改这里，用来确认线上是否已生效


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
FLOATING_STATUS_CSS = """
<style>
/* 隐藏平台自带的连接/运行状态浮层（"正在打开…"/"Running"） */
[data-testid="stStatusWidget"], [data-testid="stConnectionStatus"],
[data-testid="stAppDeployButton"], .stDeployButton { display: none !important; }
</style>
"""

FLOAT_CSS = """
<style>
/* 语言下拉浮到右上角，位于平台工具栏（Share/星标/编辑/⋮）左侧 */
.st-key-lang_box, .st-key-lang_box_login {
    position: fixed !important;
    top: 13px !important;
    right: 132px !important;
    width: 150px !important;
    z-index: 1000000 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.st-key-lang_box [data-testid="stSelectbox"], .st-key-lang_box_login [data-testid="stSelectbox"] {
    margin-bottom: 0 !important;
}
.st-key-lang_box [data-testid="stSelectbox"], .st-key-lang_box_login [data-testid="stSelectbox"] {
    transform: scale(.78) !important;
    transform-origin: right center !important;
}
.st-key-lang_box [data-baseweb="select"] > div, .st-key-lang_box_login [data-baseweb="select"] > div {
    background: transparent !important;
    border-color: rgba(128,128,128,.25) !important;
    border-radius: 8px !important;
}
</style>
"""

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
    padding-right: 0.4rem !important;
    padding-left: 0 !important;
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


def render_brand():
    # 店名占大部分，换开关单独一列贴右；语言下拉是 fixed 定位，不参与布局
    c1, _, c3 = st.columns([7.0, 0.1, 1.15])
    with c1:
        st.markdown(f"#### 🏪 {STORE_NAME}")
        st.caption(t("online"))
    with c3:
        show_toggle = st.query_params.get("debug") == "1"
        if show_toggle:
            show_debug = st.toggle(t("debug"), value=False, help=t("debug_help"))
        else:
            show_debug = False
    with st.container(key="lang_box"):
        lang_picker()
    return show_debug


def render_quick_pills():
    quick = [t("q1"), t("q2"), t("q3")]
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

    labels = ["自动（按订单/原文）", "US", "EU", "CN", "PH", "KR", "RU", "MN"]
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

    st.caption("当前接入示例数据源。合规判定在本地完成，不调用模型。")
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

    from app import handoff

    # 人工接管中：买家说啥都不进 AI，只存档等人工回
    try:
        if st.session_state.get("sid") and handoff.is_human_mode(st.session_state["sid"]):
            handoff.add_message(st.session_state["sid"], "user", text, source="buyer")
            st.session_state.history.append({"role": "user", "content": text, "ts": _now()})
            st.session_state.history.append({
                "role": "assistant",
                "content": "已转接人工客服，您的问题会由人工同事跟进，请稍候。",
                "ts": _now(),
            })
            st.session_state["handoff_active"] = True   # 继续轮询
            st.rerun()
    except Exception:
        pass

    try:
        handoff.ensure(st.session_state["sid"], language=st.session_state.get("ui_lang", "zh"))
        handoff.add_message(st.session_state["sid"], "user", text, source="buyer")
    except Exception:
        pass

    st.session_state.history.append({"role": "user", "content": text, "ts": _now()})
    with st.chat_message("user"):
        st.markdown(text)
    status = st.empty()
    status.caption(t("processing"))

    with st.spinner(t("processing")):
        try:
            # 传入上文（去掉刚追加的这条），让意图识别能看懂"就是那个订单"
            # 回复语言 = 界面语言：选了中文就回中文，选了 English 就回英文
            force_lang = st.session_state.get("ui_lang", "zh")
            trace = agent.process(text, market=market, category=category,
                                  history=st.session_state.history[:-1],
                                  force_language=force_lang)
        except Exception as e:
            st.session_state.history.append({
                "role": "assistant",
                "content": f"{t('err')} ({type(e).__name__})",
                "ts": _now(),
            })
            st.rerun()
            return

    _tool = next((s for s in trace.get("steps", []) if s.get("step") == "tool"), {})
    _order = (_tool.get("order") or {})
    st.session_state.history.append({
        "role": "assistant",
        "content": trace["final"]["text"],
        "ts": _now(),
        "language": trace["final"].get("language"),
        "order_no": _order.get("order_no"),
        "nodes": _order.get("nodes") or [],
    })
    st.session_state.last_trace = trace
    try:
        handoff.add_message(st.session_state["sid"], "assistant",
                            trace["final"]["text"], source="ai")
        if trace["final"].get("handoff"):
            handoff.mark_pending(st.session_state["sid"],
                                 reason=f"need_human · {trace['final'].get('verdict')}")
            st.session_state["handoff_active"] = True   # 开始轮询人工回复
            try:
                handoff.enter_human(st.session_state["sid"])   # 持续人工模式
            except Exception:
                pass
    except Exception:
        pass
    bump_usage()
    status.empty()
    st.rerun()




# ---------------- 商家后台 ----------------
def render_merchant():
    from app import rules_store  # noqa: F401
    import json as _json

    c1, c2 = st.columns([5, 1.4])
    with c1:
        st.markdown(f"#### 🏪 {STORE_NAME} · 商家后台")
        st.caption(f"当前账号：{st.session_state.get('user', '-')} · 规则引擎与判定统计")
    with c2:
        if st.button("退出登录", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    tab_handoff, tab_rules, tab_stats, tab_logs, tab_data = st.tabs(
        ["待处理会话", "规则库", "判定看板", "会话记录", "商品与订单"])

    with tab_handoff:
        from app import handoff
        pend = handoff.pending()
        if not pend:
            st.info("暂无待人工处理的会话。买家触发「转人工」后会出现在这里。")
        else:
            st.caption(f"待处理 {len(pend)} 条 · 回复后买家刷新页面即可看到（Streamlit 不支持实时推送）")
            for s in pend:
                with st.expander(f"会话 {s['sid']} · {s.get('created','')} · "
                                 f"{len(s.get('messages', []))} 条消息 · {s.get('reason','')}"):
                    for m in s.get("messages", []):
                        who = {"buyer": "买家", "user": "买家"}.get(m.get("role"), "AI")
                        if m.get("source") == "human":
                            who = "人工"
                        st.markdown(f"**{who}**（{m.get('ts','')}）：{m['text']}")
                    txt = st.text_area("人工回复", key=f"reply_{s['sid']}",
                                       placeholder="以人工客服身份回复买家…")
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("发送回复", key=f"send_{s['sid']}", type="primary",
                                     use_container_width=True):
                            if txt.strip():
                                handoff.human_reply(s["sid"], txt.strip())
                                handoff.mark_handled(s["sid"])
                                st.success("已发送。买家刷新页面即可看到。")
                                st.rerun()
                            else:
                                st.warning("回复内容不能为空")
                    with b2:
                        if st.button("结束会话（交还 AI）", key=f"done_{s['sid']}",
                                     use_container_width=True,
                                     help="结束后该买家的问题重新由 AI 处理"):
                            handoff.back_to_ai(s["sid"])
                            st.rerun()

    with tab_rules:
        rules = rules_store.load()
        markets = sorted({r.get("market", "-") for r in rules})
        cols = st.columns(len(markets) + 1)
        cols[0].metric("规则总数", len(rules))
        for i, mk in enumerate(markets):
            cols[i + 1].metric(mk, sum(1 for r in rules if r.get("market") == mk))

        st.divider()
        st.markdown("**导入规则**")
        st.caption("下载模板 → 填写 → 上传。导入前会逐条校验，报错会指出第几条、缺什么。")
        dl1, dl2 = st.columns(2)
        with dl1:
            tpl = (ROOT / "data" / "rules_template.json")
            if tpl.exists():
                st.download_button("下载规则模板 (JSON)", tpl.read_bytes(),
                                   file_name="rules_template.json",
                                   mime="application/json",
                                   use_container_width=True)
        with dl2:
            rd = (ROOT / "data" / "rules_template_readme.txt")
            if rd.exists():
                st.download_button("下载字段说明 (TXT)", rd.read_bytes(),
                                   file_name="rules_template_readme.txt",
                                   mime="text/plain",
                                   use_container_width=True)
        up = st.file_uploader("上传规则 JSON", type=["json"], key="rule_upload")
        if up is not None:
            try:
                data = _json.loads(up.read().decode("utf-8"))
                ok_rows, errs = rules_store.validate(data if isinstance(data, list) else data.get("rules", []))
                if errs:
                    st.error("校验未通过：\n- " + "\n- ".join(errs[:10]))
                else:
                    merged = {r["id"]: r for r in rules}
                    for r in ok_rows:
                        merged[r["id"]] = r
                    n = rules_store.save(list(merged.values()))
                    st.success(f"已导入 {len(ok_rows)} 条，当前共 {n} 条规则。")
                    st.rerun()
            except Exception as e:
                st.error(f"文件解析失败：{type(e).__name__} - {e}")

        st.divider()
        st.markdown("**当前规则（可直接编辑）**")
        edited = st.data_editor(
            rules,
            num_rows="dynamic",
            use_container_width=True,
            height=420,
            column_config={
                "id": st.column_config.TextColumn("ID", width="small"),
                "market": st.column_config.TextColumn("市场", width="small"),
                "category": st.column_config.TextColumn("品类", width="small"),
                "level": st.column_config.SelectboxColumn("级别", options=["L1", "L2", "L3"], width="small"),
                "action": st.column_config.SelectboxColumn("动作", options=["block", "rewrite", "pass"], width="small"),
                "clause": st.column_config.TextColumn("条款出处", width="large"),
                "trigger": st.column_config.TextColumn("触发条件", width="medium"),
            },
            key="rule_editor",
        )
        b1, b2, b3 = st.columns([1, 1, 2])
        with b1:
            if st.button("保存修改", type="primary", use_container_width=True):
                ok_rows, errs = rules_store.validate(list(edited))
                if errs:
                    st.error("校验未通过：\n- " + "\n- ".join(errs[:10]))
                else:
                    n = rules_store.save(ok_rows)
                    st.success(f"已保存，当前 {n} 条规则。")
                    st.rerun()
        with b2:
            vs = rules_store.versions()
            pick = st.selectbox("版本回滚", vs[:10] if vs else ["（无）"],
                                label_visibility="collapsed")
            if vs and st.button("回滚", use_container_width=True):
                rules_store.rollback(pick)
                st.success(f"已回滚到 {pick}")
                st.rerun()

    with tab_stats:
        st.caption("统计来自判定日志，随使用实时累加。")
        try:
            from app import judge_log
            s = judge_log.stats()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("累计判定", s["total"])
            m2.metric("改写/拦截占比", f"{s['rewrite_rate']}%")
            m3.metric("覆盖市场", len(s["by_market"]))
            m4.metric("覆盖语种", len(s.get("by_lang", {})) or "-")

            if s["total"]:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**市场分布**")
                    st.bar_chart(dict(sorted(s["by_market"].items())))
                with c2:
                    st.markdown("**判定结果分布**")
                    st.bar_chart(s["by_verdict"])

                c3, c4 = st.columns(2)
                with c3:
                    st.markdown("**命中条款 TOP5**")
                    if s.get("top_clauses"):
                        st.dataframe(
                            [{"条款": k, "次数": v} for k, v in s["top_clauses"]],
                            use_container_width=True, hide_index=True)
                    else:
                        st.caption("暂无拦截记录")
                with c4:
                    st.markdown("**按小时的趋势**")
                    if s.get("by_hour"):
                        st.bar_chart(dict(sorted(s["by_hour"].items())))
                    else:
                        st.caption("暂无数据")

                st.markdown("**品类分布**")
                if s.get("by_category"):
                    st.bar_chart(s["by_category"])
            else:
                st.info("还没有判定记录。去买家视角问几句就会有了。")
        except Exception as e:
            st.info(f"暂无日志。{e}")

    with tab_data:
        st.caption("当前接入的示例数据集。真实环境应通过订单接口同步。")
        try:
            orders = _json.loads((ROOT / "data" / "orders.json").read_text(encoding="utf-8"))
            products = _json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))
        except Exception as e:
            orders, products = [], []
            st.error(f"数据读取失败：{e}")

        m1, m2 = st.columns(2)
        m1.metric("订单数", len(orders))
        m2.metric("商品数", len(products))

        if products:
            st.markdown("**商品**")
            rows = []
            for p in products:
                rows.append({
                    "SKU": p.get("sku", "-"),
                    "名称": p.get("name", "-"),
                    "品类": p.get("category", "-"),
                    "市场": p.get("market", "-"),
                    "售价": p.get("price", "-"),
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

        if orders:
            st.markdown("**订单**")
            rows = []
            for o in orders:
                rows.append({
                    "订单号": o.get("order_no", "-"),
                    "买家": o.get("customer", "-"),
                    "市场": o.get("market", "-"),
                    "状态": o.get("status", "-"),
                    "承运商": o.get("carrier", "-"),
                    "运单号": o.get("tracking_no", "-"),
                    "节点数": len(o.get("nodes") or []),
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

            st.markdown("**订单物流详情**")
            pick = st.selectbox("选择订单", [o.get("order_no") for o in orders],
                                label_visibility="collapsed")
            sel = next((o for o in orders if o.get("order_no") == pick), None)
            if sel and sel.get("nodes"):
                st.dataframe(
                    [{"时间": n.get("time", "-"), "地点": n.get("place", "-"),
                      "状态": n.get("status", "-")} for n in sel["nodes"]],
                    use_container_width=True, hide_index=True)

    with tab_logs:
        try:
            from app import judge_log
            recs = judge_log.tail(30)
            if recs:
                for r in reversed(recs):
                    st.markdown(
                        f"`{r.get('ts','')}` **{r.get('market','-')}** · "
                        f"{r.get('verdict','-')} · {(r.get('text','') or '')[:60]}")
            else:
                st.info("还没有判定记录。去买家视角问几句就会有了。")
        except Exception as e:
            st.info(f"暂无日志。{e}")


@st.fragment(run_every=4)
def _poll_human_replies():
    """只有在「转人工进行中」时才轮询，避免空闲时白耗资源。"""
    if not st.session_state.get("handoff_active"):
        return
    sid = st.session_state.get("sid")
    if not sid or not st.session_state.get("authed"):
        return
    if st.session_state.get("role") != "buyer":
        return
    try:
        from app import handoff
        news = handoff.pull_replies(sid)
    except Exception:
        return
    # 人工结束了会话 → 停止轮询
    try:
        if not handoff.is_human_mode(sid):
            st.session_state["handoff_active"] = False
            return
    except Exception:
        pass

    if news:
        for r in news:
            st.session_state.setdefault("history", []).append({
                "role": "assistant",
                "content": "**【人工客服】** " + r["text"],
                "ts": r.get("ts", ""),
            })
        st.rerun(scope="app")


def main():
    if not login_gate():
        return

    st.session_state.setdefault("history", [])
    st.session_state.setdefault("last_trace", None)
    st.session_state.setdefault("dbg_market", "自动（按订单/原文）")
    st.session_state.setdefault("dbg_category", "cosmetic")
    st.session_state.setdefault("dbg_order", "（不用）")
    st.session_state.setdefault("role", "buyer")

    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    st.markdown(FLOAT_CSS, unsafe_allow_html=True)
    st.markdown(FLOATING_STATUS_CSS, unsafe_allow_html=True)
    if st.session_state.get("role") == "merchant":
        render_merchant()
        return

    # 会话 sid 写进 URL —— st.session_state 不跨刷新，URL 可以
    _sid = st.query_params.get("sid") or st.session_state.get("sid")
    if not _sid:
        import uuid as _uuid
        _sid = _uuid.uuid4().hex[:10]
        try:
            st.query_params["sid"] = _sid
        except Exception:
            pass
    st.session_state["sid"] = _sid

    show_debug = render_brand()

    if show_debug:
        chat_col, side = st.columns([1.55, 1], gap="large")
    else:
        chat_col, side = st.container(), None

    with chat_col:
        # 拉取人工回复（买家刷新时能看到）
        _pull_sid = st.query_params.get("sid") or st.session_state.get("sid")
        if _pull_sid:
            st.session_state["sid"] = _pull_sid
        if st.session_state.get("sid"):
            try:
                from app import handoff as _ho
                for _r in _ho.pull_replies(st.session_state["sid"]):
                    st.session_state.history.append({
                        "role": "assistant",
                        "content": "**【人工客服】** " + _r["text"],
                        "ts": _r.get("ts", _now()),
                    })
            except Exception:
                pass

        if not st.session_state.history:
            with st.chat_message("assistant"):
                st.markdown(t("welcome"))
                st.caption(t("lang_hint"))
            render_quick_pills()
        for msg in st.session_state.history:
            with st.chat_message(msg.get("role", "assistant")):
                st.markdown(msg["content"])
                if msg.get("ts"):
                    st.caption(msg["ts"])
                # 有物流节点就直接画路线图，买家视角也能看到进度
                if msg.get("nodes"):
                    try:
                        st.image(_route_image(msg["nodes"], msg.get("order_no") or ""),
                                 use_container_width=True)
                        with st.expander("轨迹明细"):
                            st.markdown(_timeline_md(msg["nodes"]))
                    except Exception:
                        pass

    if side is not None:
        with side:
            render_debug_panel()

    _poll_human_replies()

    # 快捷问题触发
    if st.session_state.get("pending"):
        text = st.session_state.pop("pending")
        _run_turn(text)
        return

    # 额度检查
    used = load_usage()
    if used >= DAILY_LIMIT:
        st.caption(t("quota"))
        return

    placeholder = t("placeholder")
    text = st.chat_input(placeholder)
    if text:
        _run_turn(text)


main()
