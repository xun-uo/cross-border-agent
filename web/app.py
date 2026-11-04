# -*- coding: utf-8 -*-
"""跨境智服 Agent · Streamlit 演示界面

启动：
  .venv\\Scripts\\python.exe -m streamlit run web\\app.py --server.port 8501
"""
import html as _html
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

# 「处理过程」面板的文案：单独一张表，不并进 TEXTS——
# 这份面板只在 ?debug=1 时出现，属于技术视图，没必要和买家界面共用一套 key。
# 面板里那些具体值（intent 名、verdict、订单字段）保持原样，本来就是代码里的枚举。
DBG = {
    "zh": {"empty": "提交一条消息后，这里会显示每一层的输入输出。",
           "block": "判定：拦截", "rewrite": "判定：改写",
           "ask": "判定：需要补充信息", "pass": "判定：放行",
           "clauses": "命中条款", "chain": "处理链路",
           "s_intent": "意图识别", "s_tool": "工具与检索", "s_draft": "生成草稿",
           "s_compliance": "合规判定", "s_semantic": "语义复核", "s_action": "处置动作",
           "route": "物流路线", "total": "总耗时", "calls": "模型调用", "times": "次"},
    "en": {"empty": "Send a message to see each pipeline stage's input and output here.",
           "block": "Verdict: blocked", "rewrite": "Verdict: rewritten",
           "ask": "Verdict: need more info", "pass": "Verdict: passed",
           "clauses": "Matched clauses", "chain": "Pipeline",
           "s_intent": "Intent", "s_tool": "Tools & retrieval", "s_draft": "Draft",
           "s_compliance": "Compliance", "s_semantic": "Semantic check", "s_action": "Action",
           "route": "Route", "total": "Total", "calls": "Model calls", "times": ""},
    "es": {"empty": "Envía un mensaje para ver la entrada/salida de cada etapa aquí.",
           "block": "Veredicto: bloqueado", "rewrite": "Veredicto: reescrito",
           "ask": "Veredicto: falta información", "pass": "Veredicto: aprobado",
           "clauses": "Cláusulas coincidentes", "chain": "Cadena de procesamiento",
           "s_intent": "Intención", "s_tool": "Herramientas y búsqueda", "s_draft": "Borrador",
           "s_compliance": "Cumplimiento", "s_semantic": "Revisión semántica",
           "s_action": "Acción", "total": "Tiempo total", "calls": "Llamadas al modelo",
           "times": ""},
    "vi": {"empty": "Gửi tin nhắn để xem đầu vào/đầu ra từng bước tại đây.",
           "block": "Kết luận: bị chặn", "rewrite": "Kết luận: viết lại",
           "ask": "Kết luận: cần thêm thông tin", "pass": "Kết luận: cho qua",
           "clauses": "Điều khoản khớp", "chain": "Chuỗi xử lý",
           "s_intent": "Nhận diện ý định", "s_tool": "Công cụ & truy xuất", "s_draft": "Soạn nháp",
           "s_compliance": "Kiểm tra tuân thủ", "s_semantic": "Kiểm tra ngữ nghĩa",
           "s_action": "Hành động", "total": "Tổng thời gian", "calls": "Lượt gọi model",
           "times": ""},
    "th": {"empty": "ส่งข้อความเพื่อดูข้อมูลเข้า/ออกของแต่ละขั้นตอนที่นี่",
           "block": "ผลตัดสิน: ถูกบล็อก", "rewrite": "ผลตัดสิน: เขียนใหม่",
           "ask": "ผลตัดสิน: ต้องข้อมูลเพิ่ม", "pass": "ผลตัดสิน: ผ่าน",
           "clauses": "ข้อกำหนดที่ตรง", "chain": "ลำดับการประมวลผล",
           "s_intent": "จำแนกเจตนา", "s_tool": "เครื่องมือและค้นคืน", "s_draft": "ร่างคำตอบ",
           "s_compliance": "ตรวจสอบข้อกำหนด", "s_semantic": "ตรวจสอบเชิงความหมาย",
           "s_action": "การดำเนินการ", "total": "เวลารวม", "calls": "เรียกโมเดล",
           "times": "ครั้ง"},
    "id": {"empty": "Kirim pesan untuk melihat input/output tiap tahap di sini.",
           "block": "Putusan: diblokir", "rewrite": "Putusan: ditulis ulang",
           "ask": "Putusan: perlu info tambahan", "pass": "Putusan: lolos",
           "clauses": "Klausul yang cocok", "chain": "Alur pemrosesan",
           "s_intent": "Klasifikasi intent", "s_tool": "Alat & pencarian", "s_draft": "Draf",
           "s_compliance": "Pemeriksaan kepatuhan", "s_semantic": "Pemeriksaan semantik",
           "s_action": "Tindakan", "total": "Total waktu", "calls": "Panggilan model",
           "times": ""},
}


_DBG_MORE = {
    "zh": {"panel": "处理过程", "params": "调试参数", "usage": "今日调用", "clear": "清空对话"},
    "en": {"panel": "Process trace", "params": "Debug params", "usage": "Calls today",
           "clear": "Clear chat"},
    "es": {"panel": "Traza del proceso", "params": "Parámetros de depuración",
           "usage": "Llamadas hoy", "clear": "Limpiar chat"},
    "vi": {"panel": "Quy trình xử lý", "params": "Tham số gỡ lỗi",
           "usage": "Lượt gọi hôm nay", "clear": "Xóa hội thoại"},
    "th": {"panel": "ขั้นตอนการประมวลผล", "params": "พารามิเตอร์ดีบัก",
           "usage": "เรียกวันนี้", "clear": "ล้างบทสนทนา"},
    "id": {"panel": "Jejak proses", "params": "Parameter debug",
           "usage": "Panggilan hari ini", "clear": "Hapus obrolan"},
}
for _k, _v in _DBG_MORE.items():
    DBG.setdefault(_k, {}).update(_v)


def td(key):
    """处理过程面板取词。缺翻译时回落中文，不会掉出 key 名。
    注意不能用 `or` 兜底——英文里 times 是空串，falsy 会被误判成没翻译。"""
    lang = st.session_state.get("ui_lang", "zh")
    d = DBG.get(lang) or DBG["zh"]
    if key in d:
        return d[key]
    return DBG["zh"].get(key, key)


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
                "route_detail": "轨迹明细",
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
                "route_detail": "Tracking detail",
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
                "route_detail": "Detalle del seguimiento",
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
    # ---- 东南亚：越南 / 泰 / 印尼 ----
    "vi": {
        "badge": "AI AGENT · 2026",
        "title": "Chăm sóc khách hàng xuyên biên giới",
        "sub": "Hệ thống CSKH thương mại xuyên biên giới · Đa ngôn ngữ · Tự kiểm tra tuân thủ",
        "account": "Tài khoản",
        "password": "Mật khẩu",
        "login": "Đăng nhập",
        "wrong": "Sai tài khoản hoặc mật khẩu",
        "acct_ph": "Email hoặc mã nhân viên",
        "pwd_ph": "Nhập mật khẩu",
        "cred_hint": "Quên mật khẩu, vui lòng liên hệ quản trị viên cửa hàng.",
        "wake_hint": "Dịch vụ tự ngủ khi rảnh, lần đầu truy cập vui lòng chờ.",
        "tab_buyer": "Người mua",
        "tab_shop": "Người bán",
        "order_no": "Mã đơn hàng",
        "order_ph": "Ví dụ ORDER20261021001",
        "phone_tail": "4 số cuối điện thoại",
        "tail_ph": "Ví dụ 0001",
        "enter_btn": "Vào",
        "err_login": "Mã đơn hàng hoặc 4 số cuối không đúng, vui lòng kiểm tra lại.",
        "bound_to": "Đơn hàng hiện tại",
        "online": "🟢 Trực tuyến",
        "welcome": "Xin chào, tôi là trợ lý CSKH của cửa hàng. Bạn có thể hỏi về vận chuyển, đổi trả hoặc sản phẩm.",
        "lang_hint": "Hỗ trợ 中文 / English / Español / Tiếng Việt / ไทย / Bahasa — hỏi bằng ngôn ngữ nào, tôi đáp bằng ngôn ngữ đó.",
        "q1": "Đơn hàng của tôi đang ở đâu?",
        "q2": "Chính sách đổi trả",
        "q3": "Tư vấn sản phẩm",
        "placeholder": "Nhập câu hỏi, ví dụ: Đơn hàng của tôi đến đâu rồi?",
        "debug": "Hiện quá trình xử lý",
        "debug_help": "Dùng cho demo: hiện kết quả từng lớp và tham số",
        "processing": "Đang xử lý…",
        "quota": "Đã hết hạn mức hôm nay, vui lòng thử lại ngày mai.",
        "quota_more": "Đã hết hạn mức hôm nay, sẽ đặt lại lúc 0 giờ.",
        "quota_tip": "Muốn xem thêm, vào trang quản trị cửa hàng: thư viện quy tắc, bảng thống kê và lịch sử hội thoại.",
        "err": "Xin lỗi, đã xảy ra lỗi, vui lòng thử lại sau.",
        "err_timeout": "Yêu cầu quá thời gian, không phải lỗi của bạn. Bấm «Thử lại» để gửi lại.",
        "err_busy": "Dịch vụ mô hình đang bận, thử lại sau vài giây.",
        "err_key": "Khóa máy chủ không hợp lệ, thử lại không có tác dụng. Liên hệ quản trị viên.",
        "err_net": "Không kết nối được dịch vụ mô hình, kiểm tra mạng rồi thử lại.",
        "retry": "Thử lại tin trước",
        "handoff_expired": "Phiên với nhân viên đã hết hạn (dịch vụ đã khởi động lại). Trợ lý AI đã được bật lại.",
        "waiting": "Đã chuyển cho nhân viên, đang chờ cửa hàng trả lời…",
        "clear": "Xóa hội thoại",
        "trace": "Quá trình xử lý",
        "params": "Tham số",
        "market": "Thị trường",
        "category": "Danh mục mặc định",
        "order": "Đơn hàng nhanh",
        "auto": "Tự động (theo đơn / ngữ cảnh)",
        "none": "(không dùng)",
                "route_detail": "Chi tiết hành trình",
"usage": "Lượt gọi hôm nay",
        "login_tab": "Đăng nhập",
        "signup_tab": "Đăng ký",
        "email": "Email",
        "email_ph": "you@example.com",
        "pwd_new": "Đặt mật khẩu",
        "pwd_confirm": "Xác nhận mật khẩu",
        "signup_btn": "Tạo tài khoản",
        "signup_ok": "Tạo thành công, hãy đăng nhập bằng email đó.",
        "err_email": "Vui lòng nhập email hợp lệ.",
        "err_pwd": "Hai mật khẩu không khớp.",
        "err_exists": "Email này đã đăng ký, hãy đăng nhập.",
        "err_short": "Mật khẩu ít nhất 6 ký tự.",
    },
    "th": {
        "badge": "AI AGENT · 2026",
        "title": "บริการลูกค้าข้ามพรมแดนอัจฉริยะ",
        "sub": "ระบบบริการลูกค้าอีคอมเมิร์ซข้ามพรมแดน · หลายภาษา · ตรวจสอบข้อกำหนดอัตโนมัติ",
        "account": "บัญชี",
        "password": "รหัสผ่าน",
        "login": "เข้าสู่ระบบ",
        "wrong": "บัญชีหรือรหัสผ่านไม่ถูกต้อง",
        "acct_ph": "อีเมลหรือรหัสพนักงาน",
        "pwd_ph": "กรอกรหัสผ่าน",
        "cred_hint": "ลืมรหัสผ่าน กรุณาติดต่อผู้ดูแลร้าน",
        "wake_hint": "ระบบจะพักเมื่อไม่มีผู้ใช้ ครั้งแรกที่เข้าโปรดรอสักครู่",
        "tab_buyer": "ผู้ซื้อ",
        "tab_shop": "ผู้ขาย",
        "order_no": "หมายเลขคำสั่งซื้อ",
        "order_ph": "เช่น ORDER20261021001",
        "phone_tail": "เลขท้ายเบอร์โทร 4 หลัก",
        "tail_ph": "เช่น 0001",
        "enter_btn": "เข้า",
        "err_login": "หมายเลขคำสั่งซื้อหรือเลขท้ายไม่ถูกต้อง กรุณาตรวจสอบแล้วลองใหม่",
        "bound_to": "คำสั่งซื้อปัจจุบัน",
        "online": "🟢 ออนไลน์",
        "welcome": "สวัสดีค่ะ ฉันเป็นผู้ช่วยบริการลูกค้าของร้านนี้ สอบถามเรื่องขนส่ง คืนสินค้า หรือสินค้าได้เลย",
        "lang_hint": "รองรับ 中文 / English / Español / Tiếng Việt / ไทย / Bahasa — ถามภาษาอะไร ฉันตอบภาษานั้น",
        "q1": "คำสั่งซื้อของฉันอยู่ไหน?",
        "q2": "นโยบายคืนสินค้า",
        "q3": "สอบถามสินค้า",
        "placeholder": "พิมพ์คำถาม เช่น คำสั่งซื้อของฉันถึงไหนแล้ว?",
        "debug": "แสดงขั้นตอนการทำงาน",
        "debug_help": "สำหรับเดโม: แสดงผลแต่ละชั้นและพารามิเตอร์",
        "processing": "กำลังดำเนินการ…",
        "quota": "โควตาวันนี้หมดแล้ว กรุณาลองใหม่พรุ่งนี้",
        "quota_more": "โควตาวันนี้หมดแล้ว จะรีเซ็ตตอนเที่ยงคืน",
        "quota_tip": "อยากดูต่อ เข้าหน้าผู้ดูแลร้าน: คลังกฎ แดชบอร์ด และประวัติการสนทนา",
        "err": "ขออภัย เกิดข้อผิดพลาด กรุณาลองใหม่ภายหลัง",
        "err_timeout": "คำขอใช้เวลานานเกินไป ไม่ใช่ความผิดของคุณ กด «ลองใหม่» เพื่อส่งอีกครั้ง",
        "err_busy": "บริการโมเดลไม่ว่าง ลองใหม่ในอีกสักครู่",
        "err_key": "คีย์เซิร์ฟเวอร์ไม่ถูกต้อง ลองใหม่ไม่ช่วย กรุณาติดต่อผู้ดูแล",
        "err_net": "เชื่อมต่อบริการโมเดลไม่ได้ ตรวจสอบเครือข่ายแล้วลองใหม่",
        "retry": "ลองใหม่ข้อความล่าสุด",
        "handoff_expired": "เซสชันกับเจ้าหน้าที่หมดอายุ (ระบบรีสตาร์ท) เปิดผู้ช่วย AI อีกครั้งแล้ว",
        "waiting": "โอนให้เจ้าหน้าที่แล้ว กำลังรอทางร้านตอบ…",
        "clear": "ล้างบทสนทนา",
        "trace": "ขั้นตอนการทำงาน",
        "params": "พารามิเตอร์",
        "market": "ตลาด",
        "category": "หมวดหมู่เริ่มต้น",
        "order": "คำสั่งซื้อด่วน",
        "auto": "อัตโนมัติ (ตามคำสั่งซื้อ / ข้อความ)",
        "none": "(ไม่ใช้)",
                "route_detail": "รายละเอียดการขนส่ง",
"usage": "เรียกใช้วันนี้",
        "login_tab": "เข้าสู่ระบบ",
        "signup_tab": "สมัครสมาชิก",
        "email": "อีเมล",
        "email_ph": "you@example.com",
        "pwd_new": "ตั้งรหัสผ่าน",
        "pwd_confirm": "ยืนยันรหัสผ่าน",
        "signup_btn": "สร้างบัญชี",
        "signup_ok": "สร้างสำเร็จ กรุณาเข้าสู่ระบบด้วยอีเมลนั้น",
        "err_email": "กรุณากรอกอีเมลที่ถูกต้อง",
        "err_pwd": "รหัสผ่านทั้งสองครั้งไม่ตรงกัน",
        "err_exists": "อีเมลนี้สมัครแล้ว กรุณาเข้าสู่ระบบ",
        "err_short": "รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร",
    },
    "id": {
        "badge": "AI AGENT · 2026",
        "title": "Layanan Pelanggan Lintas Batas",
        "sub": "Sistem layanan pelanggan lintas batas · Multibahasa · Pemeriksaan kepatuhan otomatis",
        "account": "Akun",
        "password": "Kata sandi",
        "login": "Masuk",
        "wrong": "Akun atau kata sandi salah",
        "acct_ph": "Email atau ID karyawan",
        "pwd_ph": "Masukkan kata sandi",
        "cred_hint": "Lupa kata sandi, hubungi admin toko.",
        "wake_hint": "Layanan tidur otomatis saat idle, kunjungan pertama mohon tunggu.",
        "tab_buyer": "Pembeli",
        "tab_shop": "Penjual",
        "order_no": "Nomor pesanan",
        "order_ph": "Contoh ORDER20261021001",
        "phone_tail": "4 digit terakhir nomor HP",
        "tail_ph": "Contoh 0001",
        "enter_btn": "Masuk",
        "err_login": "Nomor pesanan atau 4 digit terakhir salah, periksa lalu coba lagi.",
        "bound_to": "Pesanan saat ini",
        "online": "🟢 Online",
        "welcome": "Halo, saya asisten layanan pelanggan toko ini. Tanya soal pengiriman, pengembalian, atau produk.",
        "lang_hint": "Mendukung 中文 / English / Español / Tiếng Việt / ไทย / Bahasa — tanya dalam bahasa apa pun, saya jawab dengan bahasa yang sama.",
        "q1": "Di mana pesanan saya?",
        "q2": "Kebijakan pengembalian",
        "q3": "Tanya produk",
        "placeholder": "Tulis pertanyaan, mis. Pesanan saya sudah sampai mana?",
        "debug": "Tampilkan proses",
        "debug_help": "Untuk demo: tampilkan hasil tiap lapisan dan parameter",
        "processing": "Memproses…",
        "quota": "Kuota hari ini habis, coba lagi besok.",
        "quota_more": "Kuota hari ini habis, direset tengah malam.",
        "quota_tip": "Ingin melihat lebih, masuk panel penjual: pustaka aturan, dasbor keputusan, dan riwayat sesi.",
        "err": "Maaf, terjadi kesalahan. Coba lagi nanti.",
        "err_timeout": "Permintaan melebihi waktu, bukan kesalahan Anda. Klik «Coba lagi» untuk mengirim ulang.",
        "err_busy": "Layanan model sedang sibuk, coba lagi beberapa detik.",
        "err_key": "Kunci server tidak valid, coba lagi tidak membantu. Hubungi admin.",
        "err_net": "Tidak bisa terhubung ke layanan model, periksa jaringan lalu coba lagi.",
        "retry": "Coba lagi pesan terakhir",
        "handoff_expired": "Sesi dengan agen sudah kedaluwarsa (layanan restart). Asisten AI diaktifkan kembali.",
        "waiting": "Dialihkan ke agen manusia, menunggu balasan toko…",
        "clear": "Hapus percakapan",
        "trace": "Proses",
        "params": "Parameter",
        "market": "Pasar",
        "category": "Kategori default",
        "order": "Pesanan cepat",
        "auto": "Otomatis (dari pesanan / teks)",
        "none": "(tidak dipakai)",
                "route_detail": "Detail pelacakan",
"usage": "Panggilan hari ini",
        "login_tab": "Masuk",
        "signup_tab": "Daftar",
        "email": "Email",
        "email_ph": "you@example.com",
        "pwd_new": "Buat kata sandi",
        "pwd_confirm": "Konfirmasi kata sandi",
        "signup_btn": "Buat akun",
        "signup_ok": "Berhasil dibuat, silakan masuk dengan email tersebut.",
        "err_email": "Masukkan alamat email yang valid.",
        "err_pwd": "Kata sandi tidak sama.",
        "err_exists": "Email ini sudah terdaftar, silakan masuk.",
        "err_short": "Kata sandi minimal 6 karakter.",
    },
}

LANG_LABELS = {"中文": "zh", "English": "en", "Español": "es",
               "Tiếng Việt": "vi", "ไทย": "th", "Bahasa": "id"}
DISPLAY_LANG_LABEL = "Language / 语言 / Idioma / Ngôn ngữ / ภาษา"


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


def _retranslate_history(lang):
    """切语言后把整段对话重译一遍：AI 的回复和买家自己说的话都翻。

    2026-11-02 用户明确要求「已经发出去的消息也要跟着变」——原来只翻 AI 的、
    买家原话保持不动，切完语言还能看到一屏旧语言，看着像没生效。

    两个要点：
    1. 一次调用批量翻译，聊了 5 轮也只多花一次模型调用。
    2. **始终从原文翻**（`_raw`），不从上一次的译文翻——否则切三次语言会层层失真。
       翻失败就原样留着，不能让历史记录凭空消失。
    """
    h = st.session_state.get("history") or []
    idx = [i for i, m in enumerate(h)
           if m.get("role") in ("assistant", "user")
           and not m.get("human") and not m.get("error")   # 人工客服的话本来就是中文，不翻
           and m.get("content") and m.get("language") != lang]
    if not idx:
        return
    src = [h[i].get("_raw") or h[i]["content"] for i in idx]
    try:
        from app import agent as _agent
        out = _agent.translate_batch(src, lang)
    except Exception:
        return
    if len(out) != len(idx):
        return
    for i, txt in zip(idx, out):
        txt = (txt or "").strip()
        if txt:
            h[i].setdefault("_raw", h[i]["content"])   # 首次翻译时留住原文
            h[i]["content"] = txt
            h[i]["language"] = lang
    st.session_state["history"] = h


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
        try:
            st.query_params["l"] = picked   # 写进 URL，刷新后不丢
        except Exception:
            pass
        _retranslate_history(picked)        # 历史气泡跟着换语言
        st.rerun()   # 立刻重绘，避免顶部文案还是旧语言


def gear(key_suffix=""):
    """右上角语言下拉：平时只显示当前语言，点开才列其他。"""
    lang_picker()


def _after_login(user, role, bound_order=None):
    """登录成功后统一收尾。调用方负责 st.rerun()。"""
    import uuid as _uuid
    _sid = _uuid.uuid4().hex[:10]

    # 买家退出后重新登录，接着用同一个会话（#42 用户定的方案）：
    # 只要服务端内存里还留着这个订单的会话，就把它的 sid 接上；
    # 进程重启后自然找不到，生成新 sid —— 这个「丢」是可接受的，不做落盘。
    if role == "buyer" and bound_order:
        try:
            from app import handoff as _ho
            _old = _ho.by_order(bound_order)
            if _old and _old.get("sid"):
                _sid = _old["sid"]
        except Exception:
            pass

    st.session_state.authed = True
    st.session_state.user = user
    st.session_state.role = role
    st.session_state.bound_order = bound_order
    st.session_state["sid"] = _sid
    st.session_state.history = []
    st.session_state.last_trace = None

    # 把订单号写进会话，下次登录才查得到
    if role == "buyer" and bound_order:
        try:
            from app import handoff as _ho2
            _ho2.ensure(_sid, order_no=bound_order,
                        language=st.session_state.get("ui_lang", "zh"))
        except Exception:
            pass

    # 会话标识写进 URL：session_state 不跨刷新，URL 可以。
    # 买家刷新后靠这组参数自动还原登录态 + 按 sid 捞回聊天记录。
    try:
        st.query_params["sid"] = _sid
        st.query_params["r"] = role
        if bound_order:
            st.query_params["o"] = bound_order
        if role == "merchant":
            st.query_params["m"] = user
        # 语言也进 URL：刷新后不该又变回中文
        st.query_params["l"] = st.session_state.get("ui_lang", "zh")
    except Exception:
        pass

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

    # 语言从 URL 恢复：刷新 / 换标签页都不该把界面语言丢掉
    _lq = st.query_params.get("l")
    if _lq and _lq in LANG_LABELS.values() and not st.session_state.get("ui_lang"):
        st.session_state["ui_lang"] = _lq

    # 刷新页面后 session_state 是空的，但 URL 里还留着 sid / 订单号。
    # 买家靠这组参数自动还原登录态，聊天记录再按 sid 从服务端捞回来。
    # 不还原商家：URL 里带个账号就能进后台太松了，商家刷新请重新登录。
    try:
        _q = st.query_params
        if _q.get("r") == "buyer" and _q.get("sid") and _q.get("o"):
            from app import agent as _agent
            _o = _agent.find_order(_q.get("o"))
            if _o:
                st.session_state.authed = True
                st.session_state.user = "buyer"
                st.session_state.role = "buyer"
                st.session_state.bound_order = _o["order_no"]
                st.session_state["sid"] = _q.get("sid")
                st.session_state["ui_lang"] = _q.get("l") or "zh"
                st.session_state.setdefault("history", [])
                return True
    except Exception:
        pass

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

        st.caption("%s · build %s" % (t("wake_hint"), BUILD))
    return False


# ---------------- trace 面板 ----------------
BUILD = "2026-11-04 #130 · 规则库：日本/英国市场码补齐，表格可直接新增规则（触发词列）"  # 改代码时顺手改这里，用来确认线上是否已生效


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


def _route_svg(nodes, order_no="", width=1000, height=180):
    """物流路线 SVG：线条长出来 + 节点依次亮 + 当前节点脉冲。"""
    if not nodes:
        return ""
    n = len(nodes)
    pad_l, pad_r = 70, 70
    usable = width - pad_l - pad_r
    y = 104
    step = usable / max(n - 1, 1)
    xs = [pad_l + i * step for i in range(n)]
    line_d = "M %.1f %.1f L %.1f %.1f" % (xs[0], y, xs[-1], y)

    css = (
        "<style>"
        ".rt-line{stroke:#4A6EAA;stroke-width:3;fill:none;stroke-linecap:round;"
        "stroke-dasharray:1000;stroke-dashoffset:1000;animation:rtDraw 1.1s ease-out forwards;}"
        "@keyframes rtDraw{to{stroke-dashoffset:0;}}"
        ".rt-node{opacity:0;animation:rtFade .35s ease-out forwards;}"
        ".rt-node{cursor:pointer;}"
        ".rt-node:hover circle{filter:brightness(1.4);}"
        ".rt-tip{opacity:0;transition:opacity .12s;pointer-events:none;}"
        ".rt-node:hover .rt-tip{opacity:1;}"
        "@keyframes rtFade{to{opacity:1;}}"
        ".rt-pulse{animation:rtPulse 1.9s ease-out infinite;}"
        "@keyframes rtPulse{0%{r:11;opacity:.55}70%{r:24;opacity:0}100%{r:24;opacity:0}}"
        ".rt-label{font-size:11px;fill:#6A7080;}"
        ".rt-title{font-size:13px;fill:#A8843F;font-weight:600;letter-spacing:.5px;}"
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
        # 悬停提示自己画，放在节点上方。原生 <title> 的弹窗永远吊在鼠标右下，
        # 正好盖住节点和下面那行时间，看着很别扭，位置也改不了。
        _tip_txt = "%s · %s" % ((nd.get("time") or "").strip(),
                                (nd.get("desc") or "").strip())
        if len(_tip_txt) > 36:
            _tip_txt = _tip_txt[:35] + "…"
        _tw = min(300.0, 8.4 * len(_tip_txt) + 20)
        _tx = min(max(xs[i] - _tw / 2, 4.0), width - _tw - 4)
        parts.append('<g class="rt-node" style="animation-delay:%.2fs">' % delay)
        parts.append(
            '<g class="rt-tip">'
            '<rect x="%.1f" y="%d" width="%.1f" height="22" rx="6" '
            'fill="#FFFFFF" stroke="rgba(74,110,170,.45)" stroke-width="1"/>'
            '<text x="%.1f" y="%d" text-anchor="middle" font-size="11" fill="#2B3240">%s</text>'
            '</g>' % (_tx, y - 48, _tw, _tx + _tw / 2, y - 33, _html.escape(_tip_txt)))
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
    return ('<div style="background:#F4F7FC;border-radius:12px;padding:14px 16px 6px;'
            'border:1px solid rgba(74,110,170,.22);">%s</div>' % svg)


def _node_now(nodes):
    """最新一个物流节点 + 归一化好的显示字段（#40「现在到哪了」用）。

    数据里节点只有 time / desc（英文），没有 place/status，所以这里统一兜一层，
    别在调用方各写一遍 get("place") 之类不存在的字段。
    """
    if not nodes:
        return None
    nd = nodes[-1]
    t = (nd.get("time") or "").strip()
    return {"desc": (nd.get("desc") or "").strip(),
            "time": t[5:16] if len(t) >= 16 else t}


def _route_now_html(nodes):
    """物流图下面那行「现在到哪了」。"""
    cur = _node_now(nodes)
    if not cur:
        return ""
    bits = []
    if cur["desc"]:
        bits.append("<b>%s</b>" % _html.escape(cur["desc"]))
    if cur["time"]:
        bits.append('<span class="route-when">%s</span>' % _html.escape(cur["time"]))
    return ('<div class="route-now">📍 现在到哪了：%s</div>' % " · ".join(bits))


@st.dialog("物流进度", width="large")
def _route_dialog(nodes, order_no=""):
    """点击放大：大图 + 下面一行当前进度 + 完整轨迹。

    气泡里那张图被列宽压得很小（手机尤其），放大只能另开弹窗——
    Streamlit 会拦站内 <a> 点击，所以不能用链接，必须走按钮 + dialog。
    """
    st.markdown(_route_html(nodes, order_no), unsafe_allow_html=True)
    cur = _node_now(nodes)
    if cur:
        st.markdown("**现在到哪了**：%s" % (cur["desc"] or "-"))
        if cur["time"]:
            st.caption(cur["time"])
    st.markdown(_timeline_md(nodes))


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
        st.caption(td("empty"))
        return

    final = trace.get("final", {})
    verdict = final.get("verdict", "-")
    if verdict == "block":
        st.error("%s（%s）" % (td("block"), final.get("level")))
    elif verdict == "rewrite":
        st.warning("%s（%s）" % (td("rewrite"), final.get("level")))
    elif verdict == "ask":
        st.info(td("ask"))
    else:
        st.success("%s（%s）" % (td("pass"), final.get("level") or "L3"))

    if final.get("clauses"):
        st.markdown("**%s**" % td("clauses"))
        for c in final["clauses"]:
            st.markdown(f"- {c}")

    st.markdown("**%s**" % td("chain"))
    for step in trace.get("steps", []):
        name = step["step"]
        with st.expander("%s %s　%sms" % (STEP_ICON.get(name, '·'), td("s_" + name), step['ms'])):
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
                        st.markdown("**%s**" % t("route_detail"))
                        try:
                            # 用 SVG 而不是 Pillow 图：只有矢量这张才能悬停看每站详情
                            st.markdown(_route_html(order["nodes"], order["order_no"]),
                                        unsafe_allow_html=True)
                        except Exception:
                            pass
                        with st.expander(t("route_detail")):
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
        "%s %sms　%s %s %s" % (td("total"), trace.get("ms_total"),
                                td("calls"), trace.get("usage", {}).get("calls", 0),
                                td("times"))
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
/* 登录页的语言下拉浮在右上角（那页没有我们的页头，不会冲突） */
.st-key-lang_box_login {
    position: fixed !important;
    top: 13px !important;
    right: 132px !important;
    width: 150px !important;
    z-index: 1000003 !important;
    margin: 0 !important;
    padding: 0 !important;
}
.st-key-lang_box_login [data-testid="stSelectbox"] {
    margin-bottom: 0 !important;
    transform: scale(.78) !important;
    transform-origin: right center !important;
}
.st-key-lang_box_login [data-baseweb="select"] > div {
    background: transparent !important;
    border-color: rgba(128,128,128,.25) !important;
    border-radius: 8px !important;
}
/* 语言下拉 + 退出登录：装进同一个容器（key=topbar_right / topbar_right_shop），
   再由 CSS 把它摆成一行。这样窄屏才能并排（#39）：
   原来两者分属两条独立的流（一个 container、一个 st.columns），
   窄屏下 Streamlit 把 columns 堆叠，CSS 再怎么 float 也拼不到一起。 */
.st-key-topbar_right,
.st-key-topbar_right_shop {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    flex-wrap: wrap !important;
    gap: 10px !important;
    width: auto !important;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 1000003 !important;
}
.st-key-lang_box {
    width: 150px !important;
    margin: 0 !important;
    padding: 0 !important;
}
.st-key-lang_box [data-testid="stSelectbox"] {
    margin-bottom: 0 !important;
    transform: scale(.78) !important;
    transform-origin: right center !important;
}
.st-key-lang_box [data-baseweb="select"] > div {
    background: transparent !important;
    border-color: rgba(128,128,128,.25) !important;
    border-radius: 8px !important;
}
/* 商家端的语言下拉：同样的位置，只是缩放比买家端略大一点 */
.st-key-lang_box_shop {
    width: 150px !important;
    margin: 0 !important;
    padding: 0 !important;
}
.st-key-lang_box_shop [data-testid="stSelectbox"] {
    transform: scale(.8) !important;
    transform-origin: right center !important;
    margin-bottom: 0 !important;
}
.st-key-lang_box_shop [data-baseweb="select"] > div {
    background: transparent !important;
    border-color: rgba(128,128,128,.25) !important;
    border-radius: 8px !important;
}
.st-key-buyer_logout,
.st-key-shop_logout {
    width: auto !important;
    margin: 0 !important;
}
.st-key-buyer_logout button,
.st-key-shop_logout button {
    padding: 2px 12px !important;
    font-size: .8rem !important;
    min-height: 0 !important;
    height: 32px !important;
    white-space: nowrap !important;
}
/* 桌面：这一整组浮在页头右侧（工具栏占 W-216，所以 right 取 224） */
@media (min-width: 769px) {
    .st-key-topbar_right,
    .st-key-topbar_right_shop {
        position: fixed !important;
        top: 13px !important;
        right: 224px !important;
        flex-wrap: nowrap !important;
    }
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
/* ===== 商家端「翻译成中文」：译文用浅色小字挂在原文下方，不替换原文 ===== */
.zh-trans {
    margin-top: 4px;
    padding: 4px 9px;
    border-left: 2px solid rgba(201, 168, 130, .75);
    background: rgba(201, 168, 130, .09);
    border-radius: 4px;
    font-size: .82rem;
    line-height: 1.6;
    color: rgba(122, 122, 132, .98);
}
/* ===== 物流图下面那行「现在到哪了」（#40） ===== */
.route-now {
    margin: 6px 0 2px;
    padding: 6px 10px;
    border-radius: 8px;
    background: rgba(61, 190, 120, .10);
    border-left: 3px solid #3DBE78;
    font-size: .84rem;
    line-height: 1.5;
    color: rgba(52, 60, 72, .96);
}
.route-now .route-when {
    color: rgba(140, 148, 160, .95);
    font-size: .78rem;
    margin-left: 2px;
}
/* ===== 「正在处理…」固定小条（#46①）=====
   画在聊天流里的提示会被气泡挤出视口，用户以为没发出去。
   这里固定在输入框上方，任何滚动位置都看得见。 */
.st-key-busy_bar {
    position: fixed !important;
    left: 50% !important;
    transform: translateX(-50%) !important;
    bottom: 138px !important;
    width: auto !important;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 1000010 !important;
    pointer-events: none !important;
}
.busy-pill {
    display: inline-block;
    padding: 5px 16px;
    border-radius: 999px;
    background: rgba(255, 253, 250, .97);
    border: 1px solid rgba(201, 168, 130, .65);
    box-shadow: 0 3px 14px rgba(60, 50, 40, .12);
    color: #7a5c2e;
    font-size: .82rem;
    line-height: 1.5;
    white-space: nowrap;
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

# ---------------- 样式：页头固定 + 回复框贴底 ----------------
LAYOUT_CSS = """
<style>
/* 这个版本的 Streamlit 没有 --background-color 变量，只能按系统主题写死两套 */
/* 页头用 fixed，不用 sticky：sticky 的包裹层高度正好等于页头高度，
   没有「可黏的行程」= 完全不起作用（实测 rectTop 会一路滚到 -1230） */
/* 买家端页头：纯 markdown 的固定块（走 st.columns 会让内部塌陷、文字不渲染）。
   层级必须高过 Streamlit 自带的 stHeader（z-index 约 99 万），否则被它盖住看不见。
   与右上角那排工具栏同高（60px）、垂直居中，右边留 190px 给语言下拉和平台按钮；
   背景用中性半透明 + 毛玻璃，这个版本没有主题色变量，写死任何色都会跟页面差一截。 */
.shop-head-fixed {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    /* 230 是实测出来的：右上角工具栏容器从窗口右边缘往左占 216px（Share/星标/编辑/GitHub/⋮ 全在里面），
       原来写 190 会把最左边的 Share 压掉一截。 */
    right: 230px !important;
    height: 60px !important;
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    flex-wrap: nowrap !important;
    overflow: hidden;
    z-index: 1000001 !important;
    background: transparent !important;
    backdrop-filter: blur(14px) saturate(1.2) !important;
    -webkit-backdrop-filter: blur(14px) saturate(1.2) !important;
    padding: 0 0 0 5rem !important;
    border-bottom: 1px solid rgba(128,128,128,.12);
}
/* 商家端页头也用同一个纯 HTML 固定块（fixed 容器里放 st.columns / st.button
   会让组件按原始父宽度算位置，退出按钮直接被挤出边界）。 */
/* 页头是 fixed、不占文档流，Streamlit 默认给内容区留了约 6rem 的顶部空白，
   结果第一行控件离页头还有 140px 空当。压到 4rem：比页头(60px)高一点，不会撞上。 */
.block-container, [data-testid="stMainBlockContainer"] {
    padding-top: 1.2rem !important;
}
.shop-sub { font-size: .78rem; opacity: .6; white-space: nowrap; }
.logout-link {
    margin-left: auto;
    padding: 5px 14px;
    font-size: .8rem;
    color: inherit !important;
    text-decoration: none !important;
    border: 1px solid rgba(128,128,128,.35);
    border-radius: 8px;
    white-space: nowrap;
}
.logout-link:hover { border-color: rgba(201,168,130,.85); }
/* 买家端的退出不靠最右（右上角是语言下拉，会叠），紧跟订单号 */
.logout-inline { margin-left: 12px; }
/* tabs 滚到页头下面就不动了。sticky 的父级是 tab 内容容器（高度=全部内容），
   有行程所以能粘住——页头那个之所以不能用 sticky，是它的包裹层高度正好等于自身。 */
[role="tablist"] {
    position: sticky !important;
    top: 56px !important;
    z-index: 880 !important;
    background: transparent !important;
    backdrop-filter: blur(14px) saturate(1.2) !important;
    -webkit-backdrop-filter: blur(14px) saturate(1.2) !important;
}
/* debug 开关：宽屏时放在顶栏右侧（语言下拉 + 退出那组左边），跟页头同一排。
   那组控件现在占右边缘 224~466（语言 150 + 间隙 10 + 退出 ~82），所以这里要给到 480。
   窗口窄的时候顶栏放不下，会压在订单号上，所以往下挪到页头下面。 */
.st-key-dbg_box {
    position: fixed !important;
    top: 12px !important;
    right: 480px !important;
    width: 210px !important;
    z-index: 1000002 !important;
    margin: 0 !important;
}
@media (max-width: 1180px) {
    .st-key-dbg_box {
        top: 66px !important;
        right: 1.5rem !important;
        width: 200px !important;
    }
}
/* ---------- 窄屏（手机 / 竖屏平板）----------
   #41（用户 2026-11-03 要的）：页头重新置顶。原来 #120 为了省竖屏空间改成正常流，
   但用户实测「一滚店名/语言/退出就没了」，所以要固定。
   做法是把桌面那套 60px 高栏压成**两条窄带**：
     第 1 条 0–58px：店铺名 + 在线 + 当前订单（右侧留 130px 给平台工具栏 Fork/GitHub/⋮，
                     它们在父页面里，永远盖在我们的 iframe 之上，只能让开）；
     第 2 条 62–102px：语言下拉 + 退出登录并排（#39）。
   合计占顶部 102px，比 #120 正常流时的 206px 还省，而且一直可见。 */
@media (max-width: 768px) {
    .shop-head-fixed {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 56px !important;
        padding: 4px 130px 4px 12px !important;
        flex-wrap: wrap !important;
        align-content: center !important;
        row-gap: 0 !important;
        column-gap: 8px !important;
        background: rgba(252, 251, 249, .92) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border-bottom: 1px solid rgba(128,128,128,.12) !important;
    }
    .shop-head-fixed .shop-name { font-size: .9rem !important; }
    .shop-head-fixed .shop-online { font-size: .78rem !important; }
    .shop-head-fixed .shop-order { font-size: .72rem !important; }
    .shop-head-fixed .shop-order code { font-size: .7rem !important; }
    /* 语言下拉 + 退出：第 2 条窄带，并排（#39）*/
    .st-key-topbar_right,
    .st-key-topbar_right_shop {
        position: fixed !important;
        top: 60px !important;
        left: 12px !important;
        right: 12px !important;
        flex-wrap: nowrap !important;
        justify-content: flex-start !important;
        gap: 8px !important;
        z-index: 1000003 !important;
    }
    .st-key-lang_box,
    .st-key-lang_box_shop {
        width: 138px !important;
        margin: 0 !important;
    }
    .st-key-buyer_logout,
    .st-key-shop_logout {
        width: auto !important;
        flex: 0 0 auto !important;
    }
    .st-key-lang_box [data-testid="stSelectbox"],
    .st-key-lang_box_shop [data-testid="stSelectbox"] {
        transform: scale(.9) !important;
        transform-origin: left center !important;
    }
    /* debug 开关：窄屏放到第 2 条窄带下面，仍在流里 */
    .st-key-dbg_box {
        position: static !important;
        width: auto !important;
        right: auto !important;
        margin: 2px 0 0 0 !important;
    }
    /* 内容区给两条窄带让位：56 + 4 + 40 ≈ 104 */
    [data-testid="stMainBlockContainer"] {
        padding-top: 6.6rem !important;
        padding-left: .7rem !important;
        padding-right: .7rem !important;
    }
    /* main() 注入的几段空 <style> 在窄屏同样会撑出 gap，一起清零 */
    [data-testid="stMainBlockContainer"] > div:first-child:has(.shop-head-fixed) {
        gap: 0 !important;
    }
    /* tab 行也往下让，否则会钻到第 2 条窄带底下 */
    [role="tablist"] { top: 104px !important; }
}
.st-key-dbg_box [data-testid="stWidgetLabel"] { font-size: .8rem !important; }
.st-key-dbg_box [data-testid="stWidgetLabel"] p { font-size: .8rem !important; }
/* 给固定页头让出空间，内容不从它底下钻出来。
   只对桌面生效——窄屏页头已经回到正常流，不需要这段留白（而且这段写在后面会盖掉窄屏规则）。 */
@media (min-width: 769px) {
    [data-testid="stMainBlockContainer"] {
        padding-top: 4.6rem !important;
        padding-bottom: 7rem !important;
    }
    /* 页头下面那段空白：main() 每注入一段 <style> 都会生成一个 0 高度的元素，
       而内容区是 flex + gap:16px，6 个 0 高度子元素硬是撑出 96px 空隙。
       带我们页头的页面（买家/商家）把这一层的 gap 清零，内容紧贴页头。
       登录页没有 .shop-head-fixed，不受影响（:has 不支持时也只是回到旧间距）。 */
    [data-testid="stMainBlockContainer"] > div:first-child:has(.shop-head-fixed) {
        gap: 0 !important;
    }
}
/* 页头一行：店名 / 在线 / 当前订单 */
.shop-head {
    display: flex;
    align-items: baseline;
    gap: 14px;
    flex-wrap: wrap;
    margin: 0;
}
.shop-name {
    font-size: 1.05rem;
    font-weight: 700;
    line-height: 1.4;
    white-space: nowrap;
}
/* 页头状态（#51/#127/#128，配色按用户 2026-11-04 定）：
   橙 = 非真人（🤖 AI 在线 / 👤 已转人工但还没人接）；
   绿 = 真人在线（👤 人工客服已接入）。 */
.shop-online { font-size: .82rem; white-space: nowrap; }
.shop-online.is-ai,
.shop-online.is-waiting { color: #C9784A !important; font-weight: 600; }
.shop-online.is-human { color: #2FA96A !important; font-weight: 700; }
/* 品牌金主色（2026-11-04：换回原生主题切换）。
   原来靠 .streamlit/config.toml 的 [theme] primaryColor 上色，但实测 config.toml
   里只要出现 [theme]，Streamlit 就把右上角 ⋮ 菜单里的 System/Light/Dark 主题切换
   整块藏掉（三个变体都验过）。所以把 config.toml 删了，主色改用 CSS 补。 */
[data-testid="stBaseButton-primary"] {
    background-color: #C9A882 !important;
    border-color: #C9A882 !important;
    color: #2B2118 !important;
    font-weight: 600;
}
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stBaseButton-primary"]:focus {
    background-color: #BD9868 !important;
    border-color: #BD9868 !important;
    color: #2B2118 !important;
}
[data-testid="stBaseButton-primaryFormSubmit"] {
    background-color: #C9A882 !important;
    border-color: #C9A882 !important;
    color: #2B2118 !important;
    font-weight: 600;
}
[data-testid="stBaseButton-primaryFormSubmit"]:hover,
[data-testid="stBaseButton-primaryFormSubmit"]:focus {
    background-color: #BD9868 !important;
    border-color: #BD9868 !important;
    color: #2B2118 !important;
}
/* tab 选中那条横杠 + 文字：默认是 primaryColor 的红，改成品牌金（与删 config.toml 前一致） */
.react-aria-SelectionIndicator { background-color: #C9A882 !important; }
[data-testid="stTab"][aria-selected="true"] {
    border-bottom-color: #C9A882 !important;
    color: #C9A882 !important;
}
[data-testid="stTab"][aria-selected="true"] * { color: #C9A882 !important; }
/* 店名即官网入口：点了直接跳店铺，不再单设「前往店铺官网」按钮 */
a.shop-link {
    color: inherit !important;
    text-decoration: none !important;
    cursor: pointer;
    border-bottom: 1px dashed transparent;
}
a.shop-link:hover { border-bottom-color: rgba(201,168,130,.85); }
.shop-online { font-size: .8rem; opacity: .85; white-space: nowrap; }
.shop-order { font-size: .8rem; opacity: .72; white-space: nowrap; }
.shop-order code { font-size: .92em; padding: 1px 5px; }
.shop-site {
    display: inline-block;
    margin-top: 7px;
    padding: 4px 12px;
    font-size: .8rem;
    text-decoration: none !important;
    border: 1px solid rgba(128,128,128,.35);
    border-radius: 999px;
    opacity: .88;
}
.shop-site:hover { border-color: rgba(201,168,130,.85); opacity: 1; }

/* 商家端的回复框跟在「结束会话/收起会话」下面正常排版：
   不要 fixed 到窗口底部——内容一长就盖住按钮，一短就中间空一大块。
   消息区已是固定高度，页面高度稳定，不固定也不会被顶走。
   只作用于 tab 里的那个，买家端的 sticky 保持 Streamlit 默认行为。 */
[data-testid="stTabs"] [data-testid="stChatInput"] {
    position: static !important;
    bottom: auto !important;
    z-index: auto !important;
}
/* 输入框保留 Streamlit 自己的底纹：覆盖成透明就看不出哪里能输入 */
/* 消息区高度不要在这里写！任何 height !important 都会压掉下面脚本按视口算的高度，
   而且 Streamlit 自己给的是行内样式，两边打架最后谁都不对。高度统一由脚本设置。 */
</style>
"""

# ---------------- 品牌栏 ----------------
STORE_NAME = "Niao Store"

# 页头状态标签（#51/#127）：AI、已转人工等待接入、人工已接管 —— 三种必须分得开。
# 原来只有 AI/人工两态，刚转人工（商家还没回）也写「已接入」，买家会以为已经有人在。
_STATUS_LABELS = {
    "zh": ("🤖 AI 客服在线", "👤 已转人工 · 等待客服接入", "👤 人工客服已接入"),
    "en": ("🤖 AI assistant online", "👤 Handed to a human · waiting to be picked up",
           "👤 Human agent has joined"),
    "es": ("🤖 Asistente IA en línea", "👤 Derivado a un agente · en espera",
           "👤 Agente humano conectado"),
    "vi": ("🤖 Trợ lý AI trực tuyến", "👤 Đã chuyển nhân viên · đang chờ",
           "👤 Nhân viên đã tham gia"),
    "th": ("🤖 ผู้ช่วย AI ออนไลน์", "👤 ส่งต่อเจ้าหน้าที่ · กำลังรอ",
           "👤 เจ้าหน้าที่เข้าร่วมแล้ว"),
    "id": ("🤖 Asisten AI online", "👤 Dialihkan ke agen · menunggu",
           "👤 Agen manusia bergabung"),
}


def _do_logout():
    """退出登录：清掉会话与 URL 参数，回到登录页。"""
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()


def _logout_txt():
    return {"zh": "退出登录", "en": "Sign out", "es": "Cerrar sesión",
            "vi": "Đăng xuất", "th": "ออกจากระบบ", "id": "Keluar"}.get(
                st.session_state.get("ui_lang", "zh"), "Sign out")


def render_brand():
    """买家端固定页头：店名 / 在线 / 当前订单排成一行，和右上角工具栏同高。

    - 店名本身就是官网入口（点它跳店铺），不再单设「前往店铺官网」按钮
    - 整块是纯 markdown 的 fixed div：用 st.columns 包会让包裹层塌成 0、文字不渲染
    - debug 开关挪到右上角（原来被挤到页面左边）
    """
    show_debug = False

    _bound = st.session_state.get("bound_order")
    _order = ""
    if _bound:
        _order = (f'<span class="shop-order">{t("bound_to")} '
                  f'<code>{_bound}</code></span>')

    try:
        from app import store_config as _store_mod
        _sc = _store_mod.load()
    except Exception:
        _sc = {}

    _url = (_sc.get("site_url") or "").strip()
    if _url:
        _label = _sc.get("site_label") or "前往店铺官网"
        _name = (f'<a class="shop-name shop-link" href="{_url}" target="_blank" '
                 f'rel="noopener" title="{_label}">🏪 {STORE_NAME}</a>')
    else:
        _name = f'<span class="shop-name">🏪 {STORE_NAME}</span>'

    # 页头状态按「谁在服务」区分（#51/#127）：原来不管 AI 还是人工都写「🟢 在线」，
    # 买家根本看不出人工有没有接手；#127 再加一态——刚转人工但**还没人回**时不能写「已接入」。
    _mode, _owner, _status = "ai", "", ""
    try:
        from app import handoff as _ho_st
        _s_st = _ho_st.get(st.session_state.get("sid")) or {}
        _mode = _s_st.get("mode") or "ai"
        _owner = _s_st.get("owner") or ""
        _status = _s_st.get("status") or ""
    except Exception:
        pass
    _lab = _STATUS_LABELS.get(st.session_state.get("ui_lang", "zh"), _STATUS_LABELS["zh"])
    if _mode == "human":
        if _owner:
            # 已经有人接管过（首次回复时记 owner）→ 这才是「已接入」，按用户要求用绿色
            _txt = _lab[2] + f" · {_owner}"
            _cls = "shop-online is-human"
        else:
            # 转过去了但商家一句都没回 → 只能说「等待客服接入」，橙色
            _txt = _lab[1]
            _cls = "shop-online is-waiting"
    else:
        _txt = _lab[0]
        _cls = "shop-online is-ai"
    _online_html = '<span class="%s">%s</span>' % (_cls, _txt)

    st.markdown(
        f'<div class="shop-head-fixed">'
        f'{_name}'
        f'{_online_html}'
        f'{_order}'
        f'</div>',
        unsafe_allow_html=True)

    if st.query_params.get("debug") == "1":
        with st.container(key="dbg_box"):
            # 必须给固定 key：toggle 的 label 会跟着语言变，Streamlit 按 label
            # 生成内部 id，切一次语言开关就被重置成关闭，面板看起来「消失」了。
            show_debug = st.toggle(t("debug"), key="dbg_toggle",
                                   help=t("debug_help"))
    # 语言下拉 + 退出登录装进同一个容器，CSS 把它摆成一行（窄屏也并排，见 #39）。
    # 退出登录只能用真按钮：页头里放 <a href="?logout=1"> 实测点不动——
    # Streamlit 会拦截站内链接的点击，导航不完整，会话清不掉。
    with st.container(key="topbar_right"):
        with st.container(key="lang_box"):
            lang_picker()
        if st.button(_logout_txt(), key="buyer_logout"):
            _do_logout()
    return show_debug


def render_quick_pills():
    quick = [t("q1"), t("q2"), t("q3")]
    cols = st.columns(len(quick))
    for c, q in zip(cols, quick):
        if c.button(q, use_container_width=True, key=f"quick_{q}"):
            st.session_state["pending"] = q
            st.rerun()


def render_debug_panel():
    st.markdown("##### " + td("panel"))
    render_trace(st.session_state.last_trace)

    st.divider()
    st.markdown("##### " + td("params"))
    used = load_usage()
    st.progress(min(used / DAILY_LIMIT, 1.0),
                text="%s %s / %s" % (td("usage"), used, DAILY_LIMIT))

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
    if st.button(td("clear"), use_container_width=True):
        st.session_state.history = []
        st.session_state.last_trace = None
        st.rerun()

    st.caption("当前接入示例数据源。合规判定在本地完成，不调用模型。")
    st.caption(f"build {BUILD}")


def _now():
    """气泡时间：北京时间。线上容器是 UTC，直接用 datetime.now() 会慢 8 小时（#44）。"""
    from app import clock
    return clock.hhmm()


def _run_turn(text, image=None):
    """执行一轮问答并写回历史。

    image：买家随这条消息附的图片路径（#49 起「图 + 文字」走正常 AI 流程）。
    """
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
            handoff.add_message(st.session_state["sid"], "user",
                                text or "买家发来一张图片",
                                source="buyer", image=image)
            st.session_state.history.append({"role": "user", "content": text,
                                             "ts": _now(), "image": image})
            # 这里不要再插「已转接人工客服」的提示：买家页头上已经有持续的
            # 「已转人工，正在等待商家回复…」，每发一句都插一条会把对话淹掉。
            st.session_state["handoff_active"] = True   # 继续轮询
            st.rerun()
    except Exception:
        pass

    try:
        handoff.ensure(st.session_state["sid"],
                       order_no=st.session_state.get("bound_order") or "",
                       language=st.session_state.get("ui_lang", "zh"))
        handoff.add_message(st.session_state["sid"], "user",
                            text or "买家发来一张图片",
                            source="buyer", image=image)
    except Exception:
        pass

    st.session_state.history.append({"role": "user", "content": text,
                                     "ts": _now(), "image": image})
    with st.chat_message("user"):
        if text:
            st.markdown(text)
        if image:
            try:
                st.image(image, use_container_width=True)
            except Exception:
                pass
    # 「正在处理」必须**固定可见**：原来只是画在聊天流里的 caption，手机上气泡一多就被
    # 滚出视口，用户以为没发出去、又发一遍，于是出现两条重复回复（#46①）。
    # 现在做成贴在输入框上方的固定小条（样式见 LAYOUT_CSS 的 .st-key-busy_bar）。
    with st.container(key="busy_bar"):
        st.markdown(f'<div class="busy-pill">⏳ {t("processing")}</div>',
                    unsafe_allow_html=True)

    # 只用上面那条固定小条做反馈：`st.spinner` 会在聊天流里再画一个「正在处理…」，
    # 于是同一时刻出现两个提示（#46 复测时看得很明显），这里去掉 spinner。
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
    """买家发图（#49 用户 2026-11-03 定的规则）。

    - **图 + 文字**：图片落地存档后，按文字走正常 AI 流程 ——
      文字里有「退 / 换 / 破损 / 漏发 / 赔偿」这类，照样会转人工；
    - **纯图没文字**：只回一句「补一句说明」，**不转人工**。
      原来是无条件 `enter_human`，结果买家发个表情包也进人工池，人工被垃圾图占满。
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

    text = (text or "").strip()
    if text:
        # 图 + 文字：交给正常流程（含意图识别、合规、转人工判据）
        _run_turn(text, image=path)
        return

    try:
        handoff.ensure(sid,
                       order_no=st.session_state.get("bound_order") or "",
                       language=st.session_state.get("ui_lang", "zh"))
        handoff.add_message(sid, "user", "买家发来一张图片",
                            source="buyer", image=path)
    except Exception:
        pass
    st.session_state.history.append({"role": "user", "content": "",
                                     "image": path, "ts": _now()})

    note = ("图片收到了。方便补一句说明吗？"
            "（比如：外包装破损 / 漏发少件 / 尺寸或颜色不对 / 想退货）")
    st.session_state.history.append({"role": "assistant", "content": note, "ts": _now()})
    try:
        handoff.add_message(sid, "assistant", note, source="ai")
    except Exception:
        pass
    st.rerun()


# ---------------- 商家后台 ----------------
@st.fragment(run_every=6)
def _handoff_tab():
    """待处理会话面板：每 6 秒自动刷新。

    布局刻意分成两段：顶部是所有会话的一行摘要（点「查看」展开），
    下方只渲染展开的那一个。
    回复框必须放在整页最后——Streamlit 只把「页面最后一个 chat_input」
    钉在视口底部；下面再挂按钮或列表，它就跟着内容一起被往下顶。
    """
    from app import handoff, store_config

    # 面板内的成功提示：整页 rerun 会滚回顶部，这里只重绘面板，滚动位置能留住
    _pflash = st.session_state.pop("_panel_flash", None)
    if _pflash:
        st.success(_pflash)

    # 人工回复被合规拦下来的提示（人工说的话同样要过合规引擎）。
    # 不清空：这条提示要一直留着，直到商家成功发出一条合规的消息，
    # 否则 6 秒自动刷新一过就消失，人会以为自己发出去了。
    _blk = st.session_state.get("_handoff_block")
    if _blk:
        _hits = "；".join(
            f"{h['market']} {'/'.join(h['clauses'])}"
            for h in (_blk.get("hits") or [])[:4])
        _kind = "红线拦截" if _blk.get("level") == "L1" else "需改写"
        st.error(
            f"**这句话没发出去**（{_kind}）。命中：{_hits or '—'}\n\n"
            f"原话：{_blk.get('text', '')}\n\n"
            "改掉表述再发一次。")

    # 上一轮点了「发送回复」：这一轮在输入框创建之前把它清空。
    # 直接在按钮里改 text_area 的 key 会抛异常（widget 已实例化），所以走标记延迟一步。
    for _k in [k for k in list(st.session_state.keys()) if k.startswith("_clear_")]:
        _target = _k[len("_clear_"):]
        st.session_state[_target] = ""
        st.session_state.pop(_k, None)

    # 谁先回谁接管：别的客服已经接走、且没静默超时的会话，这里不显示
    _me = st.session_state.get("user") or ""
    pend = handoff.visible_to(_me)
    if not pend:
        st.info("暂无进行中的人工会话。买家触发「转人工」后会出现在这里。")
        return
    st.caption(f"{len(pend)} 个进行中的人工会话 · 每 6 秒自动刷新 · "
               f"当前接管：{_me}")

    # 手风琴：同一时间只展开一个会话。每个会话各记一个开关的话，
    # 开第二个时第一个还开着，页面会越拉越长。
    open_sid = st.session_state.get("_hopen")
    if open_sid and not any(s["sid"] == open_sid for s in pend):
        # 展开的会话被对方关掉了，指针悬空，清掉
        st.session_state["_hopen"] = None
        open_sid = None

    # ---- 顶部：按状态分两组折叠，未回复的默认展开、已回复的默认收起 ----
    # 用 session_state 记展开状态，不用 st.expander —— fragment 每 6 秒重绘会把它重置
    groups = st.session_state.setdefault("_ggroup", {"pending": True, "done": False})
    _unread = [s for s in pend if s.get("status") == "pending"]
    _done = [s for s in pend if s.get("status") != "pending"]
    _cur_open = st.session_state.get("_hopen")

    def _render_row(s):
        sid = s["sid"]
        stt = {"pending": "待回复", "answered": "已回复",
               "handled": "已回复"}.get(s.get("status"), "-")
        is_open = (_cur_open == sid)
        c1, c2 = st.columns([5, 1])
        with c1:
            dot = "🔵 " if is_open else ""
            _own = s.get("owner")
            _own_txt = f" · 👤 已由 **{_own}** 接管" if _own else ""
            st.markdown(f"{dot}**{stt}**{_own_txt} · 会话 `{sid}` · "
                        f"{s.get('created', '')} · {len(s.get('messages', []))} 条消息")
        with c2:
            if st.button("收起" if is_open else "查看", key=f"_htog_{sid}",
                         use_container_width=True):
                st.session_state["_hopen"] = None if is_open else sid
                if not is_open:
                    # 打开会话 = 看过了，红点从这一刻起撤掉（买家再说话会重新亮）
                    try:
                        handoff.mark_viewed(sid)
                    except Exception:
                        pass
                st.rerun(scope="fragment")

    for gkey, gtitle, items, dflt in (("pending", "未回复", _unread, True),
                                      ("done", "已回复", _done, False)):
        isg = groups.get(gkey, dflt)
        arrow = "▾" if isg else "▸"
        gc1, gc2 = st.columns([5, 1])
        with gc1:
            st.markdown(f"**{arrow} {gtitle}（{len(items)}）**")
        with gc2:
            if st.button("收起" if isg else "展开", key=f"_gg_{gkey}",
                         use_container_width=True):
                groups[gkey] = not isg
                st.session_state["_ggroup"] = groups
                st.rerun(scope="fragment")
        if isg:
            if not items:
                st.caption("（没有）")
            for s in items:
                _render_row(s)

    cur = next((s for s in pend if s["sid"] == open_sid), None)
    if not cur:
        return

    sid = cur["sid"]

    # ---- 中文对照（#35）：商家多半看不懂西/越/泰语，按需翻译，结果缓存 ----
    # 只翻「买家原话」和「AI 的外文回复」；人工客服说的本来就是中文，
    # 系统提示（已接入 / 安抚话术）也不翻，否则会变得不伦不类。
    _zhmap = st.session_state.setdefault("_zh_map", {}).get(sid) or {}
    _zc1, _zc2 = st.columns([4, 1])
    with _zc1:
        if _zhmap:
            st.caption("已翻译成中文：译文以浅色小字放在原文下方，原文保留。")
        else:
            st.caption("会话是外文？点右边「翻译成中文」，只翻一次，之后一直有缓存。")
    with _zc2:
        if st.button("取消翻译" if _zhmap else "翻译成中文",
                     key=f"_zhbtn_{sid}", use_container_width=True):
            if _zhmap:
                st.session_state.setdefault("_zh_map", {}).pop(sid, None)
            else:
                _need = []
                for _i, _m in enumerate(cur.get("messages") or []):
                    _src = _m.get("source")
                    _t = (_m.get("text") or "").strip()
                    if not _t or _src in ("note", "human", "system"):
                        continue
                    if any("\u4e00" <= _c <= "\u9fff" for _c in _t):
                        continue          # 本来就含中文，不用翻
                    _need.append((_i, _t))
                if _need:
                    try:
                        from app import agent as _ag
                        _out = _ag.translate_batch([x[1] for x in _need], "zh")
                    except Exception:
                        _out = []
                    if len(_out) == len(_need):
                        st.session_state.setdefault("_zh_map", {})[sid] = {
                            str(_i): _t for (_i, _), _t in zip(_need, _out) if _t}
                        _zhmap = st.session_state["_zh_map"][sid]
                    else:
                        st.session_state["_panel_flash"] = "翻译没成功，模型这次没返回结果，再点一次试试。"
            st.rerun(scope="fragment")

    # ---- 下方：只渲染展开的那个会话 ----
    # 固定高度 + 内部滚动：消息再多也只在这个框里滚，页面总高度不变，
    # 底下的回复框就不会被顶出屏幕（tab 里的 chat_input 不会自动 sticky）。
    # 高度这里给一个较大的实参（CSS 覆盖不动 Streamlit 写的行内样式），
    # 下面再用脚本按视口微调 + 滚到最新一条。
    with st.container(border=True, height=560, key="msgbox"):
        msgs = cur.get("messages", [])
        if not msgs:
            st.caption("这个会话里还没有消息。")
        # 商家视角：自己这边发的（AI 和人工）靠右，买家靠左——和买家端正好相反
        for _mi, m in enumerate(msgs):
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
                _zh_txt = (_zhmap or {}).get(str(_mi))
                if _zh_txt:
                    st.markdown(
                        f'<div class="zh-trans">中文：{_zh_txt}</div>',
                        unsafe_allow_html=True)
                if m.get("image"):
                    try:
                        st.image(m["image"], use_container_width=True)
                    except Exception:
                        st.caption("（图片已失效）")
                if m.get("ts"):
                    who = {"buyer": "买家", "human": "人工",
                           "system": "系统"}.get(src, "AI")
                    st.caption(f"{who} · {m['ts']}")

    # 结束会话和收起并排，不用上下两行
    b1, b2 = st.columns(2)
    with b1:
        if st.button("结束会话（交还 AI）", key=f"done_{sid}",
                     use_container_width=True,
                     help="结束后该买家的问题重新由 AI 处理"):
            handoff.back_to_ai(sid)
            st.session_state["_hopen"] = None
            st.rerun(scope="fragment")
    with b2:
        if st.button("收起会话", key=f"_hclose_{sid}",
                     use_container_width=True):
            st.session_state["_hopen"] = None
            st.rerun(scope="fragment")

    # 用 chat_input 而不是 text_area：只有它能「回车即发送」，
    # 而且提交后自动清空，不用再手动清 widget 状态。
    # 放在最后 = 钉在视口底部，消息再多也不会被顶走。
    txt = st.chat_input("以人工客服身份回复买家…", key=f"reply_{sid}")
    if txt:
        _raw = txt.strip()
        # 人工说的话也要过合规：任何市场 / 品类认定违规就不发出去。
        # 这里是「AI 和人受同一套约束」的落点，不能只拦 AI。
        try:
            from app import compliance as _comp
            _ev = _comp.evaluate_all(_raw)
        except Exception:
            _ev = {"verdict": "pass", "level": "L3", "clauses": [], "hits": []}
        if _ev["verdict"] in ("block", "rewrite"):
            st.session_state["_handoff_block"] = {"text": _raw, **_ev}
            st.rerun(scope="fragment")
        else:
            nm = store_config.load().get("agent_name", "")
            handoff.human_reply(sid, _raw, agent_name=nm, agent_key=_me)
            handoff.mark_handled(sid)
            st.session_state.pop("_handoff_block", None)   # 发成功了，清掉上次的拦截提示
            st.session_state["_panel_flash"] = "已发送。买家会在 4 秒内自动收到。"
            st.rerun(scope="fragment")

    # 消息区高度按视口算 + 每次重绘后滚到最新一条。
    # 纯 CSS 改不动：Streamlit 给 height 容器写的是行内样式；滚动位置也得靠脚本。
    import streamlit.components.v1 as _stc
    _stc.html("""
<script>
(function () {
  var go = function () {
    try {
      var doc = window.parent.document;
      var box = doc.querySelector('.st-key-msgbox');
      if (!box) return;
      var h = Math.max(240, window.parent.innerHeight - 430);
      if (Math.abs(box.getBoundingClientRect().height - h) > 6) {
        box.style.height = h + 'px';
      }
      box.scrollTop = box.scrollHeight;
    } catch (e) {}
  };
  setTimeout(go, 60);
  setTimeout(go, 400);
})();
</script>
""", height=0)


@st.fragment(run_every=6)
def _tab_unread_dot():
    """「待处理会话」标签右上角的未读红点（QQ/微信那种圆形红底白数字）。

    为什么不用页头：页头是 fixed 的纯 HTML，不参与 Streamlit 的数据刷新；
    tab 行是 sticky 的，切到任何 tab 都看得见，所以红点挂在这里最可靠。
    数 = 买家最后一条比商家看过的晚的会话数（handoff.unread_count）。
    """
    from app import handoff
    try:
        n = handoff.unread_count(st.session_state.get("user") or "")
    except Exception:
        return
    # 注意：n=0 时也必须渲染一条「content:none」的样式。
    # 否则 fragment 这一轮什么都不产出，上一轮注入的 <style> 会留在 DOM 里，
    # 红点就会一直挂着不肯消失（实测踩过一次）。
    txt = "99+" if n > 99 else (str(n) if n else None)
    if txt is None:
        st.markdown(
            '<style>[role="tablist"] [role="tab"]:first-child::after'
            '{content:none !important;}</style>', unsafe_allow_html=True)
        return
    st.markdown(
        "<style>"
        # 这个版本的 tab 是 div（不是 button），按 [role="tab"] 选，别按 button 选。
        # 注意 tab 那条横杠（tablist）是 overflow:auto clip，红点只要超出它的上边界
        # 就会被裁掉（实测 top:-6px 只剩一条红边），所以必须落在 tab 自己的框里。
        '[role="tablist"] [role="tab"]:first-child{position:relative !important;}'
        '[role="tablist"] [role="tab"]:first-child::after{'
        f'content:"{txt}";position:absolute;top:1px;right:-4px;'
        "min-width:16px;height:16px;padding:0 4px;border-radius:8px;"
        "background:#e53935;color:#fff;font-size:10.5px;line-height:16px;"
        "text-align:center;font-weight:700;font-family:Arial,sans-serif;"
        "box-shadow:0 0 0 1.5px rgba(255,255,255,.95);}"
        "</style>", unsafe_allow_html=True)


def render_merchant():
    from app import rules_store  # noqa: F401
    import json as _json

    # 页头：纯 HTML 固定块，和买家端同一套样式。
    # 不在 fixed 容器里放 st.columns / st.button —— 组件会按原始父宽度算位置，
    # 退出按钮会被挤出边界、还会盖住右上角那排平台图标。
    # 退出登录改成 ?logout=1 链接，由 main() 开头统一处理。
    _who = st.session_state.get("user", "-")
    st.markdown(
        f'<div class="shop-head-fixed">'
        f'<span class="shop-name">🏪 {STORE_NAME} · 商家后台</span>'
        f'<span class="shop-online">🟢 在线</span>'
        f'<span class="shop-sub">当前账号：{_who} · 规则引擎与判定统计</span>'
        f'</div>',
        unsafe_allow_html=True)

    # 操作成功提示：rerun 会吃掉当轮的 st.success，所以存下来下一轮再显示
    _flash = st.session_state.pop("_flash", None)
    if _flash:
        st.success(_flash)

    # 语言下拉：商家端也得有。页头是 fixed 的纯 HTML，塞不进组件，
    # 所以放在 tab 行上方右对齐（不用 fixed，避免盖住页头的退出按钮）。
    # 语言下拉 + 退出登录：同一个容器摆成一行（和买家端同一套，#39）
    with st.container(key="topbar_right_shop"):
        with st.container(key="lang_box_shop"):
            lang_picker()
        if st.button(_logout_txt(), key="shop_logout"):
            _do_logout()

    # 待处理会话红点：每 6 秒按「买家最后说话 > 客服最后看过」重算
    _tab_unread_dot()

    tab_handoff, tab_rules, tab_stats, tab_logs, tab_data, tab_store = st.tabs(
        ["待处理会话", "规则库", "判定看板", "会话记录", "商品与订单", "店铺设置"])

    with tab_handoff:
        _handoff_tab()

    with tab_rules:
        rules = rules_store.load()
        # 条款出处分两种：已对照官方原文核对过的，和仍是示例待核的。
        # 这一栏必须能看到——对外说「29 条已核实」时，得指得出是哪 29 条。
        _ver = sum(1 for r in rules if not r.get("unverified"))
        _ex = len(rules) - _ver
        m1, m2, m3 = st.columns(3)
        m1.metric("规则总数", len(rules))
        m2.metric("已核对条款", _ver, help="条款出处已对照官方原文逐条核对")
        m3.metric("示例待核", _ex, help="条款出处尚未核对，数据中标注为「待核实」")
        _bym = {}
        for r in rules:
            mk = r.get("market", "-")
            _bym.setdefault(mk, [0, 0])
            _bym[mk][0] += 1
            if not r.get("unverified"):
                _bym[mk][1] += 1
        st.caption("　".join("%s %d 条（已核 %d）" % (mk, v[0], v[1])
                             for mk, v in sorted(_bym.items())))
        markets = sorted(_bym)
        cols = st.columns(len(markets))
        for i, mk in enumerate(markets):
            cols[i].metric(mk, _bym[mk][0])

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
        st.markdown("**当前规则（可直接编辑，也可以在表格底部新增一行）**")
        st.caption("触发词用「、」或逗号分隔。新增一条至少要有：ID / 市场 / 级别 / 动作 / 条款出处 / 触发条件 / 一个触发词。")
        edited = st.data_editor(
            rules_store.to_editor_rows(rules),
            num_rows="dynamic",
            use_container_width=True,
            height=420,
            column_order=["id", "market", "category", "level", "action", "clause", "trigger",
                          "触发词·中文", "触发词·英文", "豁免情形", "verified"],
            column_config={
                "id": st.column_config.TextColumn("ID", width="small"),
                "market": st.column_config.TextColumn("市场", width="small",
                                                      help="可用：" + " / ".join(rules_store.MARKETS)),
                "category": st.column_config.TextColumn("品类", width="small",
                                                        help="*=全部 / cosmetic / supplement / medical_device"),
                "level": st.column_config.SelectboxColumn("级别", options=["L1", "L2", "L3"], width="small"),
                "action": st.column_config.SelectboxColumn("动作", options=["block", "rewrite", "pass"], width="small"),
                "clause": st.column_config.TextColumn("条款出处", width="large"),
                "trigger": st.column_config.TextColumn("触发条件", width="medium"),
                "触发词·中文": st.column_config.TextColumn("触发词（中文）", width="large"),
                "触发词·英文": st.column_config.TextColumn("触发词（英文）", width="large"),
                "豁免情形": st.column_config.TextColumn("豁免情形", width="medium"),
                "verified": st.column_config.TextColumn("核对状态", width="small"),
            },
            key="rule_editor",
        )
        b1, b2, b3 = st.columns([1, 1, 2])
        with b1:
            if st.button("保存修改", type="primary", use_container_width=True):
                # 表格里的列表字段是「、」拼的文本，这里换回列表；表里看不见的
                # 字段（patterns_regex / requires）按 id 从旧规则里继承。
                _clean = rules_store.from_editor_rows(edited, rules)
                ok_rows, errs = rules_store.validate(_clean)
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
        # ===== 历史会话：处理完的会话可以点开、把整段对话重看一遍 =====
        from app import handoff as _ho
        # Streamlit 的 tabs 是一次性渲染全部内容的，切 tab 不会重新跑服务端，
        # 所以这块看到的是打开页面那一刻的快照 —— 给个刷新按钮，不然刚结束的会话不出现。
        _hc1, _hc2 = st.columns([5, 1])
        with _hc1:
            st.markdown("##### 历史会话")
        with _hc2:
            if st.button("刷新", key="logs_refresh", use_container_width=True):
                st.rerun()
        st.caption("人工交还 AI 之后的会话都在这里，点「查看」能重看整段对话。")
        _done = _ho.finished(20)
        if not _done:
            st.caption("还没有已结束的会话。")
        else:
            _fopen = st.session_state.get("_fopen")
            for s in _done:
                _sid = s["sid"]
                _isopen = (_fopen == _sid)
                _tag = "人工处理过" if s.get("had_human") else "AI 处理"
                _c1, _c2 = st.columns([5, 1])
                with _c1:
                    st.markdown(
                        f"{'🔵 ' if _isopen else ''}**{_tag}** · 会话 `{_sid}` · "
                        f"{s.get('created', '')} · {len(s.get('messages', []))} 条消息")
                with _c2:
                    if st.button("收起" if _isopen else "查看", key=f"_ftog_{_sid}",
                                 use_container_width=True):
                        st.session_state["_fopen"] = None if _isopen else _sid
                        st.rerun()
                if _isopen:
                    with st.container(border=True, height=380, key=f"fbox_{_sid}"):
                        for m in s.get("messages", []):
                            _src = m.get("source")
                            if _src == "note":
                                st.markdown(
                                    f'<div class="sys-note">{m.get("text", "")}</div>',
                                    unsafe_allow_html=True)
                                continue
                            _is_buyer = (_src in ("buyer", "user")
                                         or m.get("role") in ("buyer", "user"))
                            with st.chat_message("assistant" if _is_buyer else "user"):
                                if _is_buyer:
                                    st.markdown('<span class="no-badge"></span>',
                                                unsafe_allow_html=True)
                                st.markdown(m.get("text", ""))
                                if m.get("image"):
                                    try:
                                        st.image(m["image"], use_container_width=True)
                                    except Exception:
                                        st.caption("（图片已失效）")
                                if m.get("ts"):
                                    _who_m = {"buyer": "买家", "human": "人工",
                                              "system": "系统"}.get(_src, "AI")
                                    st.caption(f"{_who_m} · {m['ts']}")

        st.divider()

        # ===== 高危对话：只保留被拦截或改写的轮次 =====
        # 全部问答铺在这里既长又没重点，客服真正要看的是"哪几句踩线了"。
        st.markdown("##### 高危对话")
        try:
            from app import judge_log
            _all = judge_log.tail(200)
            recs = [r for r in _all if r.get("verdict") in ("block", "rewrite")]
            if not recs:
                st.info("暂无高危对话。最近 %d 轮回复都过了合规判定。" % len(_all))
            else:
                st.caption("最近 %d 轮里，%d 条回复被拦截或改写" % (len(_all), len(recs)))
                for r in reversed(recs):
                    _v = r.get("verdict", "-")
                    _icon = {"pass": "🟢", "rewrite": "🟡",
                             "block": "🔴", "handoff": "🔵"}.get(_v, "⚪")
                    _who = r.get("customer") or "未绑定订单"
                    _on = r.get("order_no") or ""
                    _head = f"{_icon} **{_who}**"
                    if _on:
                        _head += f" · `{_on}`"
                    _head += f" · {r.get('market', '-')} · {_v} · {r.get('ts', '')}"
                    with st.container(border=True):
                        st.markdown(_head)
                        st.markdown(f"**问**：{(r.get('text') or '')[:200]}")
                        _ans = (r.get("answer") or "").strip()
                        if _ans:
                            st.markdown(f"**答**：{_ans[:400]}")
                        _cl = r.get("clauses") or []
                        if _cl:
                            st.caption("命中条款：" + "；".join(_cl))
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
    # 退出登录走 ?logout=1 链接：fixed 页头里放不了 st.button，
    # 用 query 参数触发一次 rerun 把会话清掉。
    try:
        if st.query_params.get("logout"):
            _do_logout()
    except Exception:
        pass

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
    st.markdown(LAYOUT_CSS, unsafe_allow_html=True)
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
        # 店名 / 在线 / 当前订单 / 官网入口已经挪到 render_brand() 的固定页头里
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

        # 刷新页面后 history 是空的，但这段对话还在服务端（sid 就在 URL 里）。
        # 按 sid 把整段捞回来，同一个账号重新进来能看到之前聊过什么。
        # 注意顺序：必须在下面 pull_replies 之前恢复，并把游标推到末尾，
        # 否则人工回复会被重复加一遍。
        if not st.session_state.history and st.session_state.get("sid") and _hs:
            try:
                _restored = []
                for _m in (_hs.get("messages") or []):
                    _src = _m.get("source")
                    _txt = _m.get("text", "")
                    if _src in ("buyer", "user"):
                        _restored.append({"role": "user", "content": _txt,
                                          "ts": _m.get("ts", ""),
                                          "image": _m.get("image")})
                    elif _src == "note":
                        _restored.append({"role": "note", "content": _txt,
                                          "ts": _m.get("ts", "")})
                    else:
                        _restored.append({"role": "assistant", "content": _txt,
                                          "ts": _m.get("ts", ""),
                                          "human": (_src == "human"),
                                          "image": _m.get("image")})
                if _restored:
                    st.session_state.history = _restored
                    _ho.pull_replies(st.session_state["sid"])   # 游标推到末尾
                    st.session_state["handoff_active"] = (_hs.get("mode") == "human")
            except Exception:
                pass

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
        for _mi, msg in enumerate(st.session_state.history):
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
                    _nodes = msg["nodes"]
                    try:
                        st.markdown(_route_html(_nodes, msg.get("order_no") or ""),
                                    unsafe_allow_html=True)
                        st.markdown(_route_now_html(_nodes), unsafe_allow_html=True)
                        # 手机上气泡里的图被压得很小，给一个放大入口（#40）
                        if st.button("🔍 点开放大", key=f"zoom_route_{_mi}",
                                     use_container_width=True):
                            _route_dialog(_nodes, msg.get("order_no") or "")
                        with st.expander(t("route_detail")):
                            st.markdown(_timeline_md(_nodes))
                    except Exception:
                        try:
                            st.image(_route_image(_nodes, msg.get("order_no") or ""),
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
