# -*- coding: utf-8 -*-
"""端到端演示脚本：跑 5 个场景 + 1 组误杀对比，结果写入 out/demo_result.json。

用法：python run_demo.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app import agent, compliance, llm  # noqa: E402

OUT_DIR = ROOT / "out"
OUT_DIR.mkdir(exist_ok=True)
OUT = OUT_DIR / "demo_result.json"


def naive_wordlist_check(draft, market, category):
    """模拟“纯关键词方案”：全局一张词表、不分市场品类、无语境判定。

    这是市面上最省事的做法，也是本作品要对比的基线。
    """
    low = draft.lower()
    hits = []
    for r in compliance.load_rules():
        for p in list(r.get("patterns") or []) + list(r.get("patterns_en") or []):
            if p and p.lower() in low:
                hits.append({"rule": r["id"], "term": p, "level": r["level"]})
    return {"verdict": "block" if hits else "pass", "hits": hits}


def check_draft(draft, market, category, language):
    """草稿检查模式（质检用）：只跑合规，不改写时可看原文。"""
    ev = compliance.evaluate(draft, market, category)
    result = {
        "input": draft,
        "evaluation": ev,
        "final_text": draft,
        "rewritten": False,
        "handoff": False,
    }
    if ev["verdict"] in ("rewrite", "block"):
        final_text, passed, rounds = compliance.rewrite(draft, ev, language=language)
        result.update({
            "final_text": final_text,
            "rewritten": True,
            "rewrite_rounds": rounds,
            "rewrite_passed": passed,
            "handoff": ev["verdict"] == "block" and not passed,
        })
    return result


def run():
    scenarios = []

    def add(sid, title, payload, note=""):
        scenarios.append({"id": sid, "title": title, "note": note, **payload})
        print(f"[{sid}] {title}")

    # A · 物流查询，未给订单号 → 追问（多轮证据）
    add("A", "物流查询：未给订单号",
        {"trace": agent.process("Hi, where is my order?")},
        "演示多轮：先追问订单号")

    # B · 物流查询，带订单号 → 读库回答
    add("B", "物流查询：给订单号",
        {"trace": agent.process("My order ORDER20261021001 hasn't arrived. Where is it?")},
        "演示工具调用与事实约束")

    # C · 破损退款 —— 模型被约束后的真实回答
    add("C", "破损退款（对客模式）",
        {"trace": agent.process("The product arrived broken. I want a full refund immediately. "
                                "Order ORDER20261021015", market="US")},
        "演示生成+合规全链路")

    # D · 破损退款 —— 违规草稿进合规层（质检模式）
    add("D", "违规草稿被自动改写（质检模式）",
        {"draft_check": check_draft(
            "No problem, we will refund you 100% right away. We guarantee delivery in 2 days.",
            "US", "cosmetic", "en")},
        "演示自动改写，而不是给建议")

    # E · 膳食补充剂疾病宣称 → 硬拦截
    add("E", "疾病宣称硬拦截（US 膳食补充剂）",
        {"draft_check": check_draft(
            "This supplement can cure insomnia and anxiety.",
            "US", "supplement", "en")},
        "演示条款级拦截 + 安全话术")

    # F · 转人工
    add("F", "法律威胁转人工",
        {"trace": agent.process("I will report you to the platform and sue you. Order ORDER20261021007")},
        "演示转人工触发")

    # G · 误杀对比（杀手演示）
    killer = ("Our product contains no hormones and cannot treat skin disease. "
              "Please consult a doctor.")
    naive = naive_wordlist_check(killer, "US", "cosmetic")
    ours = compliance.evaluate(killer, "US", "cosmetic")
    add("G", "误杀对比：含风险词但合规",
        {"comparison": {
            "input": killer,
            "naive_keyword": naive,
            "claim_level": ours,
        }},
        "纯词表误杀 vs 宣称级放行")

    result = {
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "scenarios": scenarios,
        "usage": llm.usage_snapshot(),
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {OUT}")
    print(f"llm calls: {result['usage']}")


if __name__ == "__main__":
    run()
