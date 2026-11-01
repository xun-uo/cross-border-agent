# -*- coding: utf-8 -*-
"""合规四级流水线：切分宣称 → 语境判定 → 规则匹配 → 分级动作。"""
import json
import re

from .config import DATA_DIR
from . import llm

_RULES = None
_RULES_MTIME = None
_MARKET_FALLBACK = {"LATAM": "US", "*": "US"}
_KNOWN_MARKETS = None

# 句末切分：中文标点后切；英文句号后面必须跟空白才切（避免 No.1 / 1.5% 被切断）
_BOUNDARY = re.compile(r"(?<=[。！？])|(?<=[.!?])(?=\s)")


def _rules_path():
    """商家后台编辑写的是 rules_runtime.json；合规引擎必须读同一份。

    曾经这里只读 rules.json，导致后台改了规则、启停了规则，判定结果一点不变——
    界面上说「改一处全店立即生效」，实际改了个寂寞。两边必须指向同一个文件。
    """
    p = DATA_DIR / "rules_runtime.json"
    return p if p.exists() else DATA_DIR / "rules.json"


def load_rules():
    """带 mtime 的缓存：后台保存后文件变了就重载，不需要重启服务。"""
    global _RULES, _RULES_MTIME, _KNOWN_MARKETS
    p = _rules_path()
    try:
        mt = p.stat().st_mtime
    except OSError:
        mt = None
    if _RULES is None or mt != _RULES_MTIME:
        _RULES = json.loads(p.read_text(encoding="utf-8"))
        _RULES_MTIME = mt
        _KNOWN_MARKETS = None
    return _RULES


def known_markets():
    """规则表里真实存在的市场。原来只认 CN/EU/US，PH/KR/RU/MN 会被静默
    映射成 US，那 20 条规则永远不会命中。"""
    global _KNOWN_MARKETS
    if _KNOWN_MARKETS is None:
        _KNOWN_MARKETS = {r["market"] for r in load_rules()}
    return _KNOWN_MARKETS


def resolve_market(market):
    market = (market or "US").upper()
    if market in known_markets():
        return market
    return _MARKET_FALLBACK.get(market, "US")


def rules_for(market, category):
    """category="**" 表示不过滤品类（人工回复用，因为不知道买家买的是什么）。"""
    market = resolve_market(market)
    out = []
    for r in load_rules():
        if r["market"] != market:
            continue
        if category != "**" and r["category"] != "*" and r["category"] != category:
            continue
        out.append(r)
    return out


def split_claims(text):
    text = (text or "").strip()
    if not text:
        return []
    parts = [p.strip() for p in _BOUNDARY.split(text) if p and p.strip()]
    return [p for p in parts if len(p) >= 3]


def _is_exempt(claim_low, rule):
    for pat in rule.get("exempt") or []:
        if pat.lower() in claim_low:
            return True, pat
    return False, None


# ---------------- 通用否定语境判定 ----------------
# 客服话术里最常见的合规写法就是“本产品不能治疗……”。触发词落在否定语境里就必须豁免，
# 否则误杀率会高到不可用。这是词表方案最大的坑。
_NEG_EN = re.compile(
    r"\b(?:not|never|no|cannot|can't|won't|don'?t|doesn'?t|didn'?t|isn'?t|aren'?t|without)\b",
    re.I,
)
_NEG_ZH = re.compile(r"不承诺|不能|无法|不含|不具|不会|不是|并非|不保证|不支持|不予|不可|不涉及|不用于|不提供|不做|不存在")
# 这些短语里的 no 不构成否定，否则 "No problem, we will refund…" 会被误豁免
_NEG_EXCLUDE = ("no problem", "no worries", "no doubt", "not only", "nothing but", "no questions")


def _negated(claim_low, term, window=64):
    idx = claim_low.find(term.lower())
    if idx < 0:
        return False
    ctx = claim_low[max(0, idx - window):idx]
    for ex in _NEG_EXCLUDE:
        if ex in ctx:
            return False
    return bool(_NEG_EN.search(ctx) or _NEG_ZH.search(ctx))


_EN_WORDY = re.compile(r"^[a-z0-9][a-z0-9 ,\-'\.]*$")


def _match_patterns(claim_low, rule):
    """返回命中的表述列表。

    英文表述按词边界匹配，避免 heal 命中 healthcare 这类子串误判；
    中文与含特殊符号的表述仍用子串匹配。
    """
    terms = []
    for p in list(rule.get("patterns") or []) + list(rule.get("patterns_en") or []):
        if not p:
            continue
        pl = p.lower()
        if _EN_WORDY.match(pl):
            if re.search(r"(?<![a-z])" + re.escape(pl) + r"(?![a-z])", claim_low):
                terms.append(p)
        elif pl in claim_low:
            terms.append(p)
    for rx in rule.get("patterns_regex") or []:
        try:
            m = re.search(rx, claim_low, re.I)
            if m:
                terms.append(m.group(0))
        except re.error:
            continue
    return terms


def match_claims(draft, market, category):
    """对草稿逐句匹配规则，返回逐句明细。

    两类规则：
    - 禁止型（默认）：claim 命中 patterns 即违规，除非 claim 自身含 exempt 表述；
    - 条件型（带 requires）：claim 命中 patterns 后，还要检查**全文**是否已满足前置条件
      （如必须附免责声明）。全文满足则不判违规。
    """
    rules = rules_for(market, category)
    full_low = (draft or "").lower()
    claims = split_claims(draft)
    detail = []
    for claim in claims:
        low = claim.lower()
        hits = []
        exempt_hits = []
        for r in rules:
            exempt, pat = _is_exempt(low, r)
            if exempt:
                exempt_hits.append({"rule": r["id"], "clause": r["clause"], "by": pat})
                continue
            terms = _match_patterns(low, r)
            if not terms:
                continue
            # 否定语境豁免：所有触发词都处于否定语境才豁免（避免半句否定、半句肯定被整体放行）
            if terms and all(_negated(low, t) for t in terms):
                exempt_hits.append({
                    "rule": r["id"], "clause": r["clause"],
                    "by": "否定语境：" + " / ".join(terms),
                })
                continue
            req = r.get("requires") or []
            if req and any(x.lower() in full_low for x in req):
                exempt_hits.append({
                    "rule": r["id"], "clause": r["clause"],
                    "by": "全文已含前置条件：" + " / ".join(req),
                })
                continue
            hits.append({
                "rule": r["id"],
                "clause": r["clause"],
                "trigger": r["trigger"],
                "level": r["level"],
                "terms": terms,
            })
        detail.append({
            "text": claim,
            "exempt": bool(exempt_hits) and not hits,
            "exempt_by": exempt_hits,
            "hits": hits,
        })
    return detail


def _level_rank(level):
    return {"L1": 3, "L2": 2, "L3": 1}.get(level, 0)


def evaluate(draft, market="US", category="*"):
    """纯规则判定，不调用模型。返回结构化结果。"""
    detail = match_claims(draft, market, category)
    all_hits = [h for c in detail for h in c["hits"]]
    if not all_hits:
        level = "L3"
    else:
        top = max(all_hits, key=lambda h: _level_rank(h["level"]))
        level = top["level"]

    verdict = {"L1": "block", "L2": "rewrite", "L3": "pass"}[level]
    clauses = []
    for h in all_hits:
        if h["clause"] not in clauses:
            clauses.append(h["clause"])

    if level == "L1":
        reason = "命中红线条款：" + "；".join(clauses)
    elif level == "L2":
        reason = "存在需改写的表述：" + "；".join(clauses)
    else:
        reason = "未命中任何规则，放行"

    return {
        "verdict": verdict,
        "level": level,
        "claims": detail,
        "clauses": clauses,
        "reason": reason,
        "market": resolve_market(market),
        "category": category,
    }


# ---------------- 人工回复：全市场判定 ----------------
_LEVEL_ORDER = {"L3": 0, "L2": 1, "L1": 2}


def evaluate_all(text, category="**"):
    """人工客服发的话：对全部市场判一遍，取最严重的那条。

    人工回复不预设买家在哪个市场、买的什么品类，所以按最严处理——
    任何一个市场 / 品类认定违规，都不该发出去。
    """
    worst = {"verdict": "pass", "level": "L3", "clauses": [],
             "market": None, "reason": "未命中任何市场的规则", "hits": []}
    for m in sorted(known_markets()):
        ev = evaluate(text, market=m, category=category)
        if ev["level"] == "L3":
            continue
        worst["hits"].append({
            "market": m, "level": ev["level"],
            "clauses": ev["clauses"], "reason": ev["reason"],
        })
        if _LEVEL_ORDER[ev["level"]] > _LEVEL_ORDER[worst["level"]]:
            worst.update({
                "verdict": ev["verdict"], "level": ev["level"],
                "clauses": ev["clauses"], "market": m,
                "reason": ev["reason"],
            })
    return worst


# ---------------- 生成前：注入禁止清单 ----------------

def forbidden_brief(market, category, limit=8):
    """给生成用的“禁止清单”，只取 L1，避免 prompt 过长。"""
    rules = [r for r in rules_for(market, category) if r["level"] == "L1"]
    lines = []
    for r in rules[:limit]:
        terms = (r.get("patterns") or []) + (r.get("patterns_en") or [])
        lines.append(f"- 禁止（{r['clause']}）：{r['trigger']}，如 {' / '.join(terms[:6])}")
    return "\n".join(lines)


# ---------------- 生成后：自动改写 + 复检 ----------------

LANG_NAME = {"en": "English", "es": "Spanish", "de": "German", "fr": "French",
             "zh": "Chinese", "vi": "Vietnamese", "th": "Thai", "id": "Indonesian"}

_FALLBACK = {
    "en": "I'm sorry, I can't confirm that here. Let me have a colleague check it and get back to you shortly.",
    "es": "Lo siento, no puedo confirmarlo aquí. Un compañero lo revisará y te responderá en breve.",
    "de": "Es tut mir leid, das kann ich hier nicht bestätigen. Ein Kollege prüft es und meldet sich in Kürze.",
    "fr": "Je suis désolé, je ne peux pas le confirmer ici. Un collègue vérifie et vous répondra rapidement.",
    "zh": "很抱歉，这里无法确认这一点，我先请同事核实后尽快回复您。",
    "vi": "Xin lỗi, tôi không thể xác nhận điều này ở đây. "
          "Tôi sẽ nhờ đồng nghiệp kiểm tra và phản hồi bạn sớm.",
    "th": "ขออภัยค่ะ ฉันยืนยันเรื่องนี้ที่นี่ไม่ได้ "
          "จะให้เพื่อนร่วมงานตรวจสอบแล้วติดต่อกลับโดยเร็วค่ะ",
    "id": "Maaf, saya tidak bisa memastikan hal itu di sini. "
          "Saya akan minta rekan kami memeriksanya dan segera menghubungi Anda.",
}


def fallback_reply(language):
    return _FALLBACK.get(language, _FALLBACK["en"])


def rewrite(draft, evaluation, language="en", max_rounds=2):
    """让模型按命中条款重写，并对改写结果复检。返回 (final_text, passed, rounds)。"""
    lang = LANG_NAME.get(language, "English")
    hits_desc = []
    for c in evaluation["claims"]:
        for h in c["hits"]:
            hits_desc.append(f"- 句子「{c['text']}」命中 {h['clause']}（{h['trigger']}），违规词：{', '.join(h['terms'])}")

    current = draft
    for round_no in range(1, max_rounds + 1):
        extra = ""
        if evaluation.get("market") == "US" and evaluation.get("category") == "supplement":
            extra = (
                "5. 若改写后仍保留睡眠、放松、情绪等结构/功能类表述，必须同时附上这句免责声明："
                "\"This statement has not been evaluated by the FDA. This product is not intended "
                "to diagnose, treat, cure, or prevent any disease.\"\n"
            )
        prompt = (
            "你是跨境电商客服话术改写助手。下面这句回复违反了下述合规条款，请改写成合规、自然、"
            f"可以直接发给买家的 {lang} 话术。\n\n"
            "改写要求：\n"
            "1. 保持原意与客服语气，不要生硬删词后留下病句；\n"
            "2. 不得新增任何承诺、疗效、时效保证；\n"
            "3. 不得提及“合规”“条款”“违规”等内部词汇；\n"
            "4. 只输出改写后的这一句话/几句话，不要解释。\n"
            + extra +
            f"\n原文：{current}\n\n命中条款：\n" + "\n".join(hits_desc)
        )
        try:
            new_text = llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=300,
            ).strip()
        except Exception:
            new_text = ""
        if not new_text:
            continue
        recheck = evaluate(new_text, evaluation["market"], evaluation["category"])
        if recheck["verdict"] == "pass":
            return new_text, True, round_no
        current = new_text
    return fallback_reply(language), False, max_rounds
