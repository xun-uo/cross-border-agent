# -*- coding: utf-8 -*-
"""语义兜底层：规则层放行后，对「含可疑表述」的草稿做二次判定。

设计权衡：
- 规则层快、准、可解释，但泛化差（未枚举的修辞会漏）。
- 语义层慢、泛化好，但可能过度拦截。
- 因此只在「规则层放行 + 文本含可疑信号」时触发，控制调用量。
- 语义层只判「是否违规」，不做改写——改写仍走既有流程，保证输出质量。
"""
import json

from . import llm

# 可疑信号：出现这些词/结构，但规则层没命中时，值得让语义层复核一遍
SUSPICIOUS = [
    # 英文：疗效、绝对化、承诺、功效
    "treat", "cure", "heal", "prevent", "diagnose", "reverse", "relieve",
    "best", "no.1", "number one", "100%", "guarantee", "guaranteed", "always",
    "permanent", "instantly", "proven", "clinically", "safe for all", "risk-free",
    # 中文
    "治疗", "治愈", "根治", "根治", "消炎", "抗癌", "防癌", "最好", "第一",
    "国家级", "100%", "保证", "绝对", "永久", "立刻见效", "无效退款",
]

SEM_SYS = """你是跨境电商客服的合规复核员。你的任务只有一个：判断给定回复中是否包含**明确违规**的表述。

判定原则（非常重要）：
1. 只拦截**明确违规**，不确定一律放行。运营需要的是不被误拦。
2. 以下情况**不算违规**：否定式表述（"不能治疗""不承诺"）、免责声明、转介建议（"请咨询医生"）、
   对政策的客观陈述、对物流的估计而非保证。
3. 以下情况**算违规**：向买家承诺疗效/治愈、使用绝对化最高级、承诺法规或政策不允许的赔付/退货、
   对时效做保证性承诺。

输出严格 JSON：
{
  "violation": true/false,
  "level": "L1 | L2 | L3",
  "clause": "若违规，给出大致依据（如 广告法第九条 / FDA DSHEA / 商家售后政策），否则空字符串",
  "reason": "一句话说明判据，中文，20 字以内"
}
不要输出任何解释文字。"""


def should_check(draft, intent=None):
    """决定是否走语义复核。

    - 质检模式（intent=None，直接审草稿）：一律复核，宁可多花一次调用。
    - 对客模式：只有「产品咨询 / 投诉 / 合规敏感」类回答才复核，物流与售后类交给规则层。
    """
    if intent is None:
        return True
    it = (intent.get("intent") or "").lower()
    flags = intent.get("flags") or []
    return it in ("product_inquiry", "complaint") or "compliance_sensitive" in flags


def check(draft, market, category):
    """返回与 compliance.evaluate 同构的结果；无法判定时返回 None。"""
    prompt = (f"市场：{market}\n品类：{category}\n\n"
              f"待审回复：\n{draft}\n\n请判断是否明确违规。")
    try:
        data = llm.chat_json(
            [{"role": "system", "content": SEM_SYS},
             {"role": "user", "content": prompt}],
            temperature=0, max_tokens=200)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None
    violation = bool(data.get("violation"))
    level = str(data.get("level") or ("L1" if violation else "L3"))
    if level not in ("L1", "L2", "L3"):
        level = "L2" if violation else "L3"
    if not violation:
        level = "L3"

    verdict = {"L1": "block", "L2": "rewrite", "L3": "pass"}[level]
    clause = str(data.get("clause") or "").strip()
    reason = str(data.get("reason") or "").strip()
    return {
        "verdict": verdict,
        "level": level,
        "claims": [],
        "clauses": [clause] if clause else [],
        "reason": f"语义层：{reason}" if reason else "语义层判定",
        "market": market,
        "category": category,
        "source": "semantic",
    }
