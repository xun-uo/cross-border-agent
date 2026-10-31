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
        "tab_buyer": "买家",
        "tab_shop": "商家",
        "order_no": "订单号",
        "order_ph": "例如 ORDER20261021001",
        "phone_tail": "手机号后四位",
        "tail_ph": "例如 0001",
        "enter_btn": "进入",
        "err_login": "订单号或手机尾号不对，请检查后重试。",
        "bound_to": "当前订单",
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
        "quota_more": "今日体验额度已用完，明天 0 点自动重置。",
        "quota_tip": "想继续看系统能力，可以切到商家后台看规则库、判定看板与会话记录。",
        "err": "抱歉，处理出错了，请稍后重试。",
        "err_timeout": "这次响应超时了，不是你的问题。可以点「重试上一条」再发一次。",
        "err_busy": "模型服务当前繁忙，稍等几秒再试。",
        "err_key": "服务端密钥失效，重试无效，请联系管理员。",
        "err_net": "连不上模型服务，检查网络后重试。",
        "retry": "重试上一条",
        "handoff_expired": "人工会话已过期（服务重启过），已为你重新启用 AI 助手。",
        "waiting": "已转人工，正在等待商家回复…",
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
        "tab_buyer": "Buyer",
        "tab_shop": "Merchant",
        "order_no": "Order number",
        "order_ph": "e.g. ORDER20261021001",
        "phone_tail": "Last 4 digits of phone",
        "tail_ph": "e.g. 0001",
        "enter_btn": "Enter",
        "err_login": "Order number or phone digits don't match. Please check and retry.",
        "bound_to": "Current order",
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
        "quota_more": "Daily demo quota reached. It resets at midnight.",
        "quota_tip": "To keep exploring, switch to the merchant console for the rule library, judgement stats and session log.",
        "err": "Sorry, something went wrong. Please retry.",
        "err_timeout": "The request timed out — not your fault. Tap 'Retry last message' to send it again.",
        "err_busy": "The model service is busy right now. Try again in a few seconds.",
        "err_key": "Server API key is invalid; retrying won't help. Please contact the admin.",
        "err_net": "Can't reach the model service. Check your connection and retry.",
        "retry": "Retry last message",
        "handoff_expired": "The human session has expired (the service restarted). AI assistant is back on.",
        "waiting": "Handed over to a human agent — waiting for a reply…",
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
        "tab_buyer": "Comprador",
        "tab_shop": "Comercio",
        "order_no": "Número de pedido",
        "order_ph": "p. ej. ORDER20261021001",
        "phone_tail": "Últimos 4 dígitos del teléfono",
        "tail_ph": "p. ej. 0001",
        "enter_btn": "Entrar",
        "err_login": "El pedido o los dígitos no coinciden. Revíselos y reintente.",
        "bound_to": "Pedido actual",
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
        "quota_more": "Cuota diaria de la demo agotada. Se reinicia a medianoche.",
        "quota_tip": "Para seguir explorando, entra al panel del comercio: biblioteca de reglas, estadísticas y registro de sesiones.",
        "err": "Lo siento, ocurrió un error. Reintenta.",
        "err_timeout": "La solicitud se agotó por tiempo — no es culpa suya. Pulse «Reintentar» para enviarla de nuevo.",
        "err_busy": "El servicio del modelo está ocupado. Inténtelo en unos segundos.",
        "err_key": "La clave del servidor no es válida; reintentar no ayudará. Contacte con el administrador.",
        "err_net": "No se puede conectar con el servicio del modelo. Revise la red y reintente.",
        "retry": "Reintentar el último mensaje",
        "handoff_expired": "La sesión con el agente humano ha caducado (el servicio se reinició). El asistente AI vuelve a estar activo.",
        "waiting": "Transferido a un agente humano — esperando respuesta…",
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


def _friendly_error(e):
    """把底层异常翻译成用户能看懂、也能据此行动的一句话。

    区分超时 / 限流 / 密钥 / 网络四种可分辨的情况，剩下的才归到通用错误。
    不把异常类名直接甩给买家看。
    """
    import re
    s = f"{type(e).__name__}: {e}".lower()
    if "timeout" in s or "timed out" in s:
        return t("err_timeout")
    if re.search(r"http 5\d\d", s) or "429" in s or "rate limit" in s:
        return t("err_busy")
    if "401" in s or "403" in s or "unauthorized" in s or "api key" in s:
        return t("err_key")
    if ("urlerror" in s or "connection" in s or "network" in s
            or "resolve" in s or "ssl" in s):
        return t("err_net")
    return t("err")


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


def _after_login(user, role, bound_order=None):
    """登录成功后统一收尾。调用方负责 st.rerun()。"""
    st.session_state.authed = True
    st.session_state.user = user
    st.session_state.role = role
    st.session_state.bound_order = bound_order
    st.session_state.history = []
    st.session_state.last_trace = None
    # 先清掉登录区再重绘，避免旧表单闪一下
    _ph = st.session_state.pop("_login_ph", None)
    if _ph is not None:
        _ph.empty()


def _verify_buyer(order_no, tail):
    """买家凭「订单号 + 手机后四位」进入。成功返回订单对象，失败返回 None。

    真实产品这里应换成短信验证码；比赛环境没有短信通道，用尾号四位代替，
    它至少证明「知道这一单 + 拿得到预留手机」，比裸订单号强一档。
    """
    from app import agent as _agent
    tail = (tail or "").strip()
    o = _agent.find_order((order_no or "").strip())
    if not o or len(tail) != 4 or (o.get("phone") or "")[-4:] != tail:
        st.error(t("err_login"))
        return None
    return o


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

    _ph = st.empty()
    st.session_state["_login_ph"] = _ph
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        st.markdown(f"## {t('title')}")
        st.caption(t("sub"))

        tab_buyer, tab_shop = st.tabs([t("tab_buyer"), t("tab_shop")])

        with tab_buyer:
            with st.form("buyer_login"):
                _no = st.text_input(t("order_no"), placeholder=t("order_ph"))
                _tail = st.text_input(t("phone_tail"), placeholder=t("tail_ph"),
                                      max_chars=4)
                _b_ok = st.form_submit_button(t("enter_btn"), use_container_width=True)
            if _b_ok:
                _o = _verify_buyer(_no, _tail)
                if _o:
                    _after_login("buyer", "buyer", _o["order_no"])
                    st.rerun()

        with tab_shop:
            with st.form("login_form"):
                acct = st.text_input(t("account"), placeholder=t("acct_ph"))
                pwd = st.text_input(t("password"), type="password", placeholder=t("pwd_ph"))
                ok = st.form_submit_button(t("login"), use_container_width=True)
            if ok:
                key = acct.strip().lower()
                rec = ACCOUNTS.get(key)
                if rec and rec[0] == pwd:
                    _after_login(key, rec[1], None)
                    st.rerun()
                else:
                    st.error(t("wrong"))
            st.caption(t("cred_hint"))

        st.caption(t("wake_hint"))
    return False


# ---------------- trace 面板 ----------------
BUILD = "2026-10-31 #86 · handoff-ui + image"  # 改代码时顺手改这里，用来确认线上是否已生效


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


def _route_svg(nodes, order_no="", width=1000, height=170):
    """物流路线 SVG：线条长出来 + 节点依次亮 + 当前节点脉冲。"""
    if not nodes:
        return ""
    n = len(nodes)
    pad_l, pad_r = 70, 70
    usable = width - pad_l - pad_r
    y = 74
    step = usable / max(n - 1, 1)
    xs = [pad_l + i * step for i in range(n)]
    line_d = "M %.1f %.1f L %.1f %.1f" % (xs[0], y, xs[-1], y)

    css = (
        "<style>"
        ".rt-line{stroke:#4A6EAA;stroke-width:3;fill:none;stroke-linecap:round;"
        "stroke-dasharray:1000;stroke-dashoffset:1000;animation:rtDraw 1.1s ease-out forwards;}"
        "@keyframes rtDraw{to{stroke-dashoffset:0;}}"
        ".rt-node{opacity:0;animation:rtFade .35s ease-out forwards;}"
        "@keyframes rtFade{to{opacity:1;}}"
        ".rt-pulse{animation:rtPulse 1.9s ease-out infinite;}"
        "@keyframes rtPulse{0%{r:11;opacity:.55}70%{r:24;opacity:0}100%{r:24;opacity:0}}"
        ".rt-label{font-size:11px;fill:#8C8478;}"
        ".rt-title{font-size:13px;fill:#C9A882;font-weight:600;letter-spacing:.5px;}"
        ".rt-tag{font-size:10px;letter-spacing:1px;}"
        "</style>"
    )

    parts = ['<svg viewBox="0 0 %d %d" width="100%%" xmlns="http://www.w3.org/2000/svg" '
             'style="font-family:-apple-system,Segoe UI,Microsoft YaHei,sans-serif;">' % (width, height)]
    parts.append(css)
    parts.append('<text class="rt-title" x="14" y="22">Route · %s</text>' % (order_no or ""))
    parts.append('<path class="rt-line" d="%s" />' % line_d)

    for i, nd in enumerate(nodes):
        last = (i == n - 1)
        delay = 0.35 + i * 0.16
        color = "#3DBE78" if last else "#4A8AF4"
        r = 11 if last else 8
        parts.append('<g class="rt-node" style="animation-delay:%.2fs">' % delay)
        if last:
            parts.append('<circle class="rt-pulse" cx="%.1f" cy="%d" r="11" fill="#3DBE78" />' % (xs[i], y))
        parts.append('<circle cx="%.1f" cy="%d" r="%d" fill="%s" stroke="#fff" stroke-width="2" />'
                     % (xs[i], y, r, color))
        parts.append("</g>")

        tm = (nd.get("time") or "")[5:16]
        parts.append('<text class="rt-label" x="%.1f" y="%d" text-anchor="middle" '
                     'style="opacity:0;animation:rtFade .35s ease-out forwards;animation-delay:%.2fs">%s</text>'
                     % (xs[i], y + 28, delay, tm))

        if i == 0:
            parts.append('<text class="rt-label rt-tag" x="%.1f" y="%d" text-anchor="middle" '
                         'style="opacity:0;animation:rtFade .35s ease-out forwards;animation-delay:%.2fs">ORIGIN</text>'
                         % (xs[i], y + 44, delay))
        if last:
            parts.append('<text class="rt-label rt-tag" x="%.1f" y="%d" text-anchor="middle" fill="#3DBE78" '
                         'style="opacity:0;animation:rtFade .35s ease-out forwards;animation-delay:%.2fs">NOW</text>'
                         % (xs[i], y + 44, delay))

    parts.append("</svg>")
    return "".join(parts)


def _route_html(nodes, order_no=""):
    svg = _route_svg(nodes, order_no)
    if not svg:
        return ""
    return ('<div style="background:#131A26;border-radius:12px;padding:14px 16px 6px;'
            'border:1px solid rgba(74,110,170,.35);">%s</div>' % svg)


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

/* 登录卡片：不要白底，跟页面背景同色，只留一圈细边 */
[data-testid="stForm"] {
    background: transparent !important;
    border: 1px solid rgba(201,168,130,.22) !important;
    border-radius: 16px !important;
    padding: 1.3rem 1.5rem !important;
}
/* 卡片里的「登录 / 注册」标签，白底时看不见，透明后按主题色走 */
[data-testid="stForm"] [data-baseweb="tab"] p {
    color: inherit !important;
}
/* 访客入口：低调描边，别抢登录主按钮的注意力 */
.st-key-guest_in button {
    background: transparent !important;
    border: 1px dashed rgba(201,168,130,.5) !important;
    color: rgba(201,168,130,1) !important;
    box-shadow: none !important;
    font-weight: 500 !important;
}
.st-key-guest_in button:hover {
    border-color: rgba(201,168,130,.9) !important;
    background: rgba(201,168,130,.08) !important;
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
    border-color: rgba(201,168,130,.45);
    background: rgba(201,168,130,.13);
}
/* 文字统一从左往右排：气泡靠右，但文字不跟着右对齐（长文本右对齐最后一行会贴边） */
/* 客服：靠左 */
[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageAvatarUser"])) > div:not([data-testid^="stChatMessageAvatar"]) {
    margin-right: auto;
    margin-left: 10px;
    text-align: left;
}
/* ===== 气泡内右上角 AI 徽章 ===== */
[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageAvatarUser"])) > div:not([data-testid^="stChatMessageAvatar"]) {
    position: relative;
    padding-right: 54px;
}
[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageAvatarUser"])) > div:not([data-testid^="stChatMessageAvatar"])::after {
    content: "AI";
    position: absolute;
    top: 8px;
    right: 10px;
    background: rgba(176,138,85,.12);
    border: 1px solid rgba(176,138,85,.45);
    border-radius: 6px;
    padding: 1px 5px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .6px;
    color: #B08A55;
    font-family: "Segoe UI", Arial, sans-serif;
    line-height: 1.4;
    pointer-events: none;
}
/* 人工客服说的话：人说的话不能标成 AI */
[data-testid="stChatMessage"]:has(.human-msg) > div:not([data-testid^="stChatMessageAvatar"])::after {
    content: none !important;
}
[data-testid="stChatMessage"]:has(.human-msg) > div:not([data-testid^="stChatMessageAvatar"]) {
    padding-right: 18px;
}
/* 商家后台里买家的话：靠左但同样不该挂 AI 徽章 */
[data-testid="stChatMessage"]:has(.no-badge) > div:not([data-testid^="stChatMessageAvatar"])::after {
    content: none !important;
}
[data-testid="stChatMessage"]:has(.no-badge) > div:not([data-testid^="stChatMessageAvatar"]) {
    padding-right: 18px;
}
/* ===== 人工接管系统提示：居中灰字，不套气泡（淘宝客服那种） ===== */
.sys-note {
    text-align: center;
    color: rgba(150, 150, 150, .95);
    font-size: 12.5px;
    line-height: 1.6;
    margin: 16px 0 12px;
}
/* 对话里的图片：气泡是 fit-content，不撑开的话图片会被压成缩略图 */
[data-testid="stChatMessage"] [data-testid="stImage"] {
    width: 100% !important;
}
[data-testid="stChatMessage"] [data-testid="stImage"] img {
    max-width: 100% !important;
    width: auto !important;
    min-width: 220px !important;
    height: auto !important;
    border-radius: 10px;
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
                "role": "note",
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
                                  force_language=force_lang,
                                  bound_order=st.session_state.get("bound_order"))
        except Exception as e:
            # 记下这条消息，界面给一个「重试上一条」的入口，而不是让用户自己重打一遍
            st.session_state["last_failed"] = text
            st.session_state.history.append({
                "role": "assistant",
                "content": _friendly_error(e),
                "ts": _now(),
                "error": True,
            })
            st.rerun()
            return

    _tool = next((s for s in trace.get("steps", []) if s.get("step") == "tool"), {})
    _order = (_tool.get("order") or {})
    _intent = next((s for s in trace.get("steps", []) if s.get("step") == "intent"), {})
    _intent_name = (_intent.get("output") or {}).get("intent")
    # 只有物流查询才画轨迹图。其他意图即便为了推断品类读了订单，也不该甩一张物流图出来
    _nodes = (_order.get("nodes") or []) if _intent_name == "logistics_query" else []
    st.session_state.history.append({
        "role": "assistant",
        "content": trace["final"]["text"],
        "ts": _now(),
        "language": trace["final"].get("language"),
        "order_no": _order.get("order_no") if _nodes else None,
        "nodes": _nodes,
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


UPLOAD_DIR = ROOT / "data" / "uploads"


def _save_upload(uploaded, sid):
    """把上传的图片落地，返回路径；失败返回 None。"""
    import time as _t
    try:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        ext = Path(uploaded.name).suffix.lower()
        if ext not in (".png", ".jpg", ".jpeg", ".webp"):
            ext = ".png"
        fn = UPLOAD_DIR / f"{(sid or 'anon')}_{int(_t.time() * 1000)}{ext}"
        fn.write_bytes(uploaded.getvalue())
        return str(fn)
    except Exception:
        return None


def _run_image_turn(text, files):
    """买家发图：图片落地 → 记进双方对话 → 直接转人工。

    图片在客服场景里基本都是证据（破损、错发、漏发），该由人看、由人定，
    所以不送进模型做识别，直接进人工队列。
    """
    from app import handoff
    sid = st.session_state.get("sid")
    path = None
    for f in (files or []):
        path = _save_upload(f, sid)
        if path:
            break
    if not path:
        st.warning("图片保存失败，请重试。")
        return

    st.session_state.history.append({
        "role": "user",
        "content": text or "",
        "image": path,
        "ts": _now(),
    })
    try:
        handoff.ensure(sid, language=st.session_state.get("ui_lang", "zh"))
        handoff.add_message(sid, "user", text or "买家发来一张图片",
                            source="buyer", image=path)
        handoff.mark_pending(sid, reason="buyer_image")
        handoff.enter_human(sid)
        st.session_state["handoff_active"] = True
    except Exception:
        pass

    note = "图片已收到，已转人工客服处理，请稍候。"
    st.session_state.history.append({"role": "note", "content": note, "ts": _now()})
    try:
        handoff.add_message(sid, "assistant", note, source="ai")
    except Exception:
        pass
    st.rerun()


# ---------------- 商家后台 ----------------
@st.fragment(run_every=6)
def _handoff_tab():
    """待处理会话面板：每 6 秒自动刷新。

    用 selectbox 选会话，不用 expander——fragment 重绘会让 expander 自动收起，
    商家正在回复时被强行折叠一次，体验很差。
    """
    from app import handoff, store_config

    # 面板内的成功提示：整页 rerun 会滚回顶部，这里只重绘面板，滚动位置能留住
    _pflash = st.session_state.pop("_panel_flash", None)
    if _pflash:
        st.success(_pflash)

    # 上一轮点了「发送回复」：这一轮在输入框创建之前把它清空。
    # 直接在按钮里改 text_area 的 key 会抛异常（widget 已实例化），所以走标记延迟一步。
    for _k in [k for k in list(st.session_state.keys()) if k.startswith("_clear_")]:
        _target = _k[len("_clear_"):]
        st.session_state[_target] = ""
        st.session_state.pop(_k, None)

    pend = handoff.pending()
    if not pend:
        st.info("暂无进行中的人工会话。买家触发「转人工」后会出现在这里。")
        return
    st.caption(f"{len(pend)} 个进行中的人工会话 · 每 6 秒自动刷新")

    for s in pend:
        sid = s["sid"]
        stt = {"pending": "待回复", "answered": "已回复",
               "handled": "已回复"}.get(s.get("status"), "-")
        open_key = f"_hopen_{sid}"
        is_open = st.session_state.get(open_key, False)

        # 不用 st.expander：面板每 6 秒重绘，expander 的展开状态会被重置，
        # 商家正在看对话时被强行收起一次。展开状态存进 session_state 才稳。
        cc1, cc2 = st.columns([5, 1])
        with cc1:
            st.markdown(f"**{stt}** · 会话 `{sid}` · {s.get('created', '')} · "
                        f"{len(s.get('messages', []))} 条消息")
        with cc2:
            if st.button("收起" if is_open else "查看", key=f"_htog_{sid}",
                         use_container_width=True):
                st.session_state[open_key] = not is_open
                st.rerun(scope="fragment")

        if is_open:
            # 商家视角：自己这边发的（AI 和人工）靠右，买家靠左——和买家端正好相反
            for m in s.get("messages", []):
                src = m.get("source")
                if src == "note":
                    st.markdown(
                        f'<div class="sys-note">{m.get("text", "")}</div>',
                        unsafe_allow_html=True)
                    continue
                is_buyer = src in ("buyer", "user") or m.get("role") in ("buyer", "user")
                with st.chat_message("assistant" if is_buyer else "user"):
                    if is_buyer:
                        # 买家的话在商家视角靠左，但它不是 AI 说的，不能挂 AI 徽章
                        st.markdown('<span class="no-badge"></span>', unsafe_allow_html=True)
                    st.markdown(m.get("text", ""))
                    if m.get("image"):
                        try:
                            st.image(m["image"], use_container_width=True)
                        except Exception:
                            st.caption("（图片已失效）")
                    if m.get("ts"):
                        who = {"buyer": "买家", "human": "人工"}.get(src, "AI")
                        st.caption(f"{who} · {m['ts']}")

            txt = st.text_area("人工回复", key=f"reply_{sid}",
                               placeholder="以人工客服身份回复买家…")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("发送回复", key=f"send_{sid}", type="primary",
                             use_container_width=True):
                    if txt.strip():
                        nm = store_config.load().get("agent_name", "")
                        handoff.human_reply(sid, txt.strip(), agent_name=nm)
                        handoff.mark_handled(sid)
                        st.session_state[f"_clear_reply_{sid}"] = True
                        st.session_state["_panel_flash"] = "已发送。买家会在 4 秒内自动收到。"
                        st.rerun(scope="fragment")
                    else:
                        st.warning("回复内容不能为空")
            with b2:
                if st.button("结束会话（交还 AI）", key=f"done_{sid}",
                             use_container_width=True,
                             help="结束后该买家的问题重新由 AI 处理"):
                    handoff.back_to_ai(sid)
                    st.rerun(scope="fragment")
        st.divider()


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

    # 操作成功提示：rerun 会吃掉当轮的 st.success，所以存下来下一轮再显示
    _flash = st.session_state.pop("_flash", None)
    if _flash:
        st.success(_flash)

    tab_handoff, tab_rules, tab_stats, tab_logs, tab_data, tab_store = st.tabs(
        ["待处理会话", "规则库", "判定看板", "会话记录", "商品与订单", "店铺设置"])

    with tab_handoff:
        _handoff_tab()

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
                    st.session_state["_flash"] = f"已导入 {len(ok_rows)} 条，当前共 {n} 条规则。"
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
                    st.session_state["_flash"] = f"已保存，当前 {n} 条规则。"
                    st.rerun()
        with b2:
            vs = rules_store.versions()
            pick = st.selectbox("版本回滚", vs[:10] if vs else ["（无）"],
                                label_visibility="collapsed")
            if vs and st.button("回滚", use_container_width=True):
                rules_store.rollback(pick)
                st.session_state["_flash"] = f"已回滚到 {pick}"
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

    with tab_store:
        from app import store_config as _store_cfg
        cfg = _store_cfg.load()
        st.caption("这里的设置改完直接对买家端生效，不需要改代码。")
        with st.form("store_cfg"):
            url = st.text_input("店铺官网地址", value=cfg.get("site_url", ""),
                                placeholder="https://your-store.com")
            label = st.text_input("跳转按钮文案", value=cfg.get("site_label", ""),
                                  placeholder="前往店铺官网")
            agent_name = st.text_input("客服对外名称", value=cfg.get("agent_name", ""),
                                       placeholder="留空则显示「人工客服」")
            saved = st.form_submit_button("保存设置", type="primary",
                                          use_container_width=True)
        if saved:
            _store_cfg.save({
                "site_url": (url or "").strip(),
                "site_label": (label or "").strip() or "前往店铺官网",
                "agent_name": (agent_name or "").strip(),
            })
            st.session_state["_flash"] = "店铺设置已保存，买家端刷新即可看到。"
            st.rerun()
        if cfg.get("site_url"):
            st.caption(f"当前跳转地址：{cfg['site_url']}")


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

    # 人工超时未回 → 自动安抚一次（不让买家干等）
    try:
        if handoff.need_comfort(sid):
            text = handoff.add_comfort_message(sid)
            if text:
                st.session_state.setdefault("history", []).append({
                    "role": "assistant",
                    "content": text,
                    "ts": "",
                })
                st.rerun(scope="app")
    except Exception:
        pass

    if news:
        for r in news:
            if r.get("source") == "note":
                st.session_state.setdefault("history", []).append({
                    "role": "note",
                    "content": r.get("text", ""),
                    "ts": r.get("ts", ""),
                })
            else:
                st.session_state.setdefault("history", []).append({
                    "role": "assistant",
                    "content": r.get("text", ""),
                    "human": True,
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
        _bound = st.session_state.get("bound_order")
        if _bound:
            st.caption(f"{t('bound_to')}：`{_bound}`")
        # 商家在后台配的官网地址：买家登录后可直接跳过去
        try:
            from app import store_config as _store_mod
            _sc = _store_mod.load()
        except Exception:
            _sc = {}
        if _sc.get("site_url"):
            st.link_button(_sc.get("site_label") or "前往店铺官网", _sc["site_url"])
        # 拉取人工回复（买家页面在人工模式下 4 秒轮询一次）
        _pull_sid = st.query_params.get("sid") or st.session_state.get("sid")
        if _pull_sid:
            st.session_state["sid"] = _pull_sid

        from app import handoff as _ho
        _hs = _ho.get(st.session_state["sid"]) if st.session_state.get("sid") else None

        # 服务重启会清空内存里的会话；此时买家还挂着「人工中」，必须说清楚，不能让他干等
        if st.session_state.get("handoff_active") and _hs is None:
            st.session_state.history.append({
                "role": "assistant",
                "content": t("handoff_expired"),
                "ts": _now(),
            })
            st.session_state["handoff_active"] = False
            _hs = None

        if st.session_state.get("sid"):
            try:
                for _r in _ho.pull_replies(st.session_state["sid"]):
                    if _r.get("source") == "note":
                        st.session_state.history.append({
                            "role": "note",
                            "content": _r.get("text", ""),
                            "ts": _r.get("ts", _now()),
                        })
                    else:
                        st.session_state.history.append({
                            "role": "assistant",
                            "content": _r.get("text", ""),
                            "human": True,
                            "ts": _r.get("ts", _now()),
                        })
            except Exception:
                pass

        # 已转人工、商家还没回：明确告诉买家现在在等谁
        if _hs and _hs.get("mode") == "human" and _hs.get("status") != "answered":
            st.caption(t("waiting"))

        if not st.session_state.history:
            with st.chat_message("assistant"):
                st.markdown(t("welcome"))
                st.caption(t("lang_hint"))
            render_quick_pills()
        for msg in st.session_state.history:
            # 系统提示（如「人工客服已接入」）：居中灰字，不套气泡
            if msg.get("role") == "note":
                st.markdown(
                    f'<div class="sys-note">{msg.get("content", "")}</div>',
                    unsafe_allow_html=True)
                continue
            with st.chat_message(msg.get("role", "assistant")):
                if msg.get("human"):
                    # 标记：CSS 用它把这句的 AI 徽章去掉
                    st.markdown('<span class="human-msg"></span>', unsafe_allow_html=True)
                st.markdown(msg["content"])
                if msg.get("image"):
                    try:
                        st.image(msg["image"], use_container_width=True)
                    except Exception:
                        st.caption("（图片已失效，请重新上传）")
                if msg.get("ts"):
                    _ts = f"人工客服 · {msg['ts']}" if msg.get("human") else msg["ts"]
                    st.caption(_ts)
                # 有物流节点就直接画路线图，买家视角也能看到进度
                if msg.get("nodes"):
                    try:
                        st.markdown(_route_html(msg["nodes"], msg.get("order_no") or ""),
                                    unsafe_allow_html=True)
                        with st.expander("轨迹明细"):
                            st.markdown(_timeline_md(msg["nodes"]))
                    except Exception:
                        try:
                            st.image(_route_image(msg["nodes"], msg.get("order_no") or ""),
                                     use_container_width=True)
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
        st.warning(t("quota_more"))
        st.caption(t("quota_tip"))
        return

    # 上一轮失败了：给一个入口重发，不用用户自己重打一遍
    if st.session_state.get("last_failed"):
        if st.button(t("retry"), key="retry_last"):
            _txt = st.session_state.pop("last_failed")
            _h = st.session_state.get("history", [])
            if _h and _h[-1].get("error"):
                _h.pop()
            if _h and _h[-1].get("role") == "user":
                _h.pop()
            _run_turn(_txt)
            return

    placeholder = t("placeholder")
    msg = st.chat_input(placeholder, accept_file=True,
                        file_type=["png", "jpg", "jpeg", "webp"],
                        max_upload_size=10)
    if msg:
        if getattr(msg, "files", None):
            _run_image_turn(getattr(msg, "text", "") or "", msg.files)
        elif getattr(msg, "text", ""):
            _run_turn(msg.text)


main()
