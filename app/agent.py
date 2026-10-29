# -*- coding: utf-8 -*-
"""主链路：意图 → 检索/工具 → 生成草稿 → 合规判定 → 改写/转人工。"""
import json
import re
import time

from .config import DATA_DIR
from . import compliance, llm, semantic

_ORDERS = None
_PRODUCTS = None
_KB = None

ORDER_RE = re.compile(r"ORDER\s*\d{8,}", re.I)


def _load(name, cache_name):
    global _ORDERS, _PRODUCTS, _KB
    store = {"orders": "_ORDERS", "products": "_PRODUCTS", "kb": "_KB"}[cache_name]
    if globals()[store] is None:
        globals()[store] = json.loads((DATA_DIR / name).read_text(encoding="utf-8"))
    return globals()[store]


def orders():
    return _load("orders.json", "orders")


def products():
    return _load("products.json", "products")


def kb():
    return _load("kb.json", "kb")


def find_order(order_no):
    if not order_no:
        return None
    norm = re.sub(r"\s+", "", order_no).upper()
    for o in orders():
        if re.sub(r"\s+", "", o["order_no"]).upper() == norm:
            return o
    return None


def extract_order_no(text):
    m = ORDER_RE.search(text or "")
    return re.sub(r"\s+", "", m.group(0)).upper() if m else None


def retrieve_kb(query, market, topic=None, limit=2):
    """极简检索：按关键词重叠打分。规则/合规不走这里。"""
    q = set(re.findall(r"[\w\u4e00-\u9fa5]+", (query or "").lower()))
    scored = []
    for item in kb():
        if item["market"] not in ("*", market):
            continue
        text = (item["title"] + " " + item["text"]).lower()
        words = set(re.findall(r"[\w\u4e00-\u9fa5]+", text))
        score = len(q & words)
        if topic and item["topic"] == topic:
            score += 3
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: -x[0])
    return [item for _, item in scored[:limit]]


# ---------------- 意图识别 ----------------

INTENT_SYS = """你是跨境电商客服系统的意图识别模块。
判断买家这句话，输出严格 JSON，字段如下：
{
  "intent": "logistics_query | return_exchange | order_change | product_inquiry | complaint | compliance_sensitive",
  "flags": ["complaint" 和/或 "compliance_sensitive"，没有就空数组],
  "emotion": "neutral | frustrated | angry",
  "language": "en | es | de | fr | zh",
  "need_human": true/false,
  "order_no": "文中出现的订单号，没有则为空字符串"
}

判定优先级（从上到下，命中即停）：
1. 涉及破损、少件、漏发、错发、退款、退货、换货 → return_exchange
2. 要求取消订单、修改收货地址或规格 → order_change
3. 询问配送范围、时效、运单号、何时送达、为何没收到 → logistics_query
4. 询问成分、用法、适用人群、价格、发票、批发、能否治愈某病 → product_inquiry
5. 涉及医疗伤害、过敏、法律诉讼、赔偿 → compliance_sensitive
6. 以上都不成立，只有抱怨、威胁、要求负责人 → complaint

关键规则：
- 语气激烈不等于 complaint。只要同时存在具体事务诉求（如"破了要退"），
  主意图归事务类，complaint 只放进 flags。
- 情绪激烈、提到曝光/起诉/平台投诉时，need_human = true。
- product_inquiry 里如果买家问"能不能治某病"，仍属 product_inquiry，但 flags 加 compliance_sensitive。
- 不要输出任何解释。"""


def classify(text, history=None):
    messages = [{"role": "system", "content": INTENT_SYS}]
    if history:
        for turn in history[-4:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
    messages.append({"role": "user", "content": text})
    try:
        data = llm.chat_json(messages, temperature=0, max_tokens=200)
    except Exception as e:
        data = {
            "intent": "product_inquiry", "flags": [], "emotion": "neutral",
            "language": "en", "need_human": False, "order_no": "",
            "error": str(e),
        }
    data.setdefault("flags", [])
    data.setdefault("order_no", "")
    if not data.get("order_no"):
        data["order_no"] = extract_order_no(text) or ""
    return data


# ---------------- 生成草稿 ----------------

GEN_SYS = """你是跨境电商客服，用买家使用的语言回复，简洁、礼貌、只陈述能确认的事实。
硬性要求：
1. 订单状态、物流、金额只能来自给定资料，绝对不许编造或推测。
2. 不得使用绝对化用语（best / No.1 / 100% safe / perfect 等）。
3. 不得作任何疾病治疗、预防、治愈的宣称。
4. 不得承诺任何超出政策的时效、退款、赔偿。
5. 只输出给买家的话，不解释过程。"""


def generate_draft(text, intent, order, kb_items, market, category, language):
    ctx = []
    if order:
        ctx.append("订单资料：\n" + json.dumps(order, ensure_ascii=False, indent=2))
    if kb_items:
        ctx.append("可用政策与手册：\n" + "\n".join(
            f"- [{i['title']}] {i['text']}" for i in kb_items))
    forbidden = compliance.forbidden_brief(market, category)
    if forbidden:
        ctx.append("本市场红线清单（不得违反）：\n" + forbidden)
    ctx.append(f"买家使用语言：{language}")

    messages = [
        {"role": "system", "content": GEN_SYS},
        {"role": "user", "content": "\n\n".join(ctx) + f"\n\n买家消息：{text}\n\n请直接给出回复。"},
    ]
    return llm.chat_hedged(messages, temperature=0.3, max_tokens=500).strip()


# ---------------- 品类自动识别 ----------------
CATEGORY_HINTS = {
    "supplement": ["supplement", "capsule", "pill", "vitamin", "melatonin", "probiotic",
                   "补充剂", "胶囊", "维生素", "保健品", "钙片"],
    "medical_device": ["device", "monitor", "thermometer", "brace", "仪器", "设备", "器械"],
    "cosmetic": ["cream", "serum", "cleanser", "lotion", "mask", "lipstick", "shampoo",
                 "面霜", "精华", "洁面", "面膜", "口红", "乳液", "护肤"],
}


def infer_category(text, fallback="cosmetic"):
    """从买家原话推断品类；订单自带的品类优先级更高（由 process 处理）。"""
    low = (text or "").lower()
    for cat, words in CATEGORY_HINTS.items():
        if any(w.lower() in low for w in words):
            return cat
    return fallback


# ---------------- 主流程 ----------------

def _usage_delta(before):
    """只统计本轮调用，而不是进程启动以来的累计值。"""
    now = llm.usage_snapshot()
    return {
        "calls": now["calls"] - before["calls"],
        "prompt_tokens": now["prompt_tokens"] - before["prompt_tokens"],
        "completion_tokens": now["completion_tokens"] - before["completion_tokens"],
    }


def process(text, market="US", category="*", history=None, force_category_from_order=True):
    t0 = time.perf_counter()
    usage_before = dict(llm.usage_snapshot())
    trace = {"input": text, "steps": [], "usage": {}, "final": {}}

    def step(name, payload, started):
        trace["steps"].append({
            "step": name,
            "ms": round((time.perf_counter() - started) * 1000),
            **payload,
        })

    # 1) 意图
    s = time.perf_counter()
    intent = classify(text, history)
    step("intent", {"output": intent}, s)

    language = intent.get("language") or "en"
    # 品类：订单优先，其次从买家原话推断，最后才用界面传入的默认值
    inferred = infer_category(text, fallback=category)
    order = find_order(intent.get("order_no"))
    if order:
        market = order["market"]
        # 买家语言优先，订单记录的语言只作兜底——买家说中文就用中文回
        language = intent.get("language") or order.get("language") or "en"
        if force_category_from_order and order["items"]:
            category = order["items"][0]["category"]
        else:
            category = inferred
    else:
        category = inferred

    # 2) 工具 / 检索
    s = time.perf_counter()
    kb_items = []
    need_order = intent["intent"] in ("logistics_query", "return_exchange")
    if need_order and not order and not intent.get("order_no"):
        step("tool", {"order": None, "note": "缺订单号，转为追问"}, s)
        trace["final"] = {
            "text": _ask_order_no(language),
            "verdict": "ask",
            "level": "L3",
            "rewritten": False,
            "handoff": False,
            "market": compliance.resolve_market(market),
            "category": category,
        }
        trace["ms_total"] = round((time.perf_counter() - t0) * 1000)
        trace["usage"] = _usage_delta(usage_before)
        return trace

    if order:
        kb_items = retrieve_kb(text, compliance.resolve_market(market),
                               topic="return_policy" if intent["intent"] == "return_exchange" else "shipping")
    else:
        kb_items = retrieve_kb(text, compliance.resolve_market(market))
    step("tool", {"order": order, "kb": [i["id"] for i in kb_items]}, s)

    # 3) 生成草稿
    s = time.perf_counter()
    draft = generate_draft(text, intent, order, kb_items,
                           compliance.resolve_market(market), category, language)
    step("draft", {"text": draft}, s)

    # 4) 合规判定
    s = time.perf_counter()
    evaluation = compliance.evaluate(draft, market, category)
    step("compliance", {"output": evaluation}, s)

    # 4.5) 语义兜底：规则放行、但草稿里带可疑表述时才复核
    s = time.perf_counter()
    if evaluation["verdict"] == "pass" and semantic.should_check(draft, intent):
        sem = semantic.check(draft, market, category)
        if sem is not None:
            step("semantic", {"output": sem,
                              "note": "命中" if sem["verdict"] != "pass" else "放行"}, s)
            if sem["verdict"] != "pass":
                evaluation = sem

    # 5) 动作
    s = time.perf_counter()
    final_text = draft
    rewritten = False
    handoff = bool(intent.get("need_human"))
    if evaluation["verdict"] in ("rewrite", "block"):
        final_text, passed, rounds = compliance.rewrite(
            draft, evaluation, language=language)
        rewritten = True
        if evaluation["verdict"] == "block" and not passed:
            handoff = True
    if handoff and not rewritten:
        final_text = final_text + "\n\n" + _handoff_note(language)
    step("action", {
        "verdict": evaluation["verdict"],
        "rewritten": rewritten,
        "handoff": handoff,
        "text": final_text,
    }, s)

    # 判定日志（供商家看板统计）
    try:
        from . import judge_log
        judge_log.append({
            "text": text, "market": compliance.resolve_market(order["market"]) if order else market,
            "category": category,
            "verdict": display_verdict, "rule_verdict": evaluation["verdict"],
            "level": evaluation.get("level"), "clauses": evaluation.get("clauses", []),
            "calls": trace["usage"].get("calls", 0),
        })
    except Exception:
        pass

    display_verdict = evaluation["verdict"]
    if display_verdict == "block" and rewritten and not handoff:
        display_verdict = "rewrite"   # 已改写成安全话术，对外说「改写」而不是「拦截」
    trace["final"] = {
        "text": final_text,
        "verdict": display_verdict,
        "rule_verdict": evaluation["verdict"],
        "level": evaluation["level"],
        "clauses": evaluation.get("clauses", []),
        "rewritten": rewritten,
        "handoff": handoff,
        "market": evaluation["market"],
        "category": category,
        "language": language,
    }
    trace["ms_total"] = round((time.perf_counter() - t0) * 1000)
    trace["usage"] = _usage_delta(usage_before)
    return trace


_ASK_ORDER = {
    "en": "Sure — could you share your order number? It usually starts with ORDER.",
    "es": "Claro, ¿me compartes tu número de pedido? Suele empezar por ORDER.",
    "de": "Gerne — könnten Sie mir Ihre Bestellnummer nennen? Sie beginnt meist mit ORDER.",
    "fr": "Bien sûr, pouvez-vous me donner votre numéro de commande ? Il commence généralement par ORDER.",
    "zh": "好的，方便发一下订单号吗？一般以 ORDER 开头。",
}
_HANDOFF = {
    "en": "I'm bringing a colleague in to help you with this.",
    "es": "Voy a pasar el caso a un compañero para que te ayude.",
    "de": "Ich ziehe eine Kollegin hinzu, die Ihnen weiterhilft.",
    "fr": "Je transmets votre demande à un collègue qui va vous aider.",
    "zh": "我请同事来协助您处理。",
}


def _ask_order_no(language):
    return _ASK_ORDER.get(language, _ASK_ORDER["en"])


def _handoff_note(language):
    return _HANDOFF.get(language, _HANDOFF["en"])
