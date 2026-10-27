# -*- coding: utf-8 -*-
"""评测脚本：合规漏杀/误杀/擦边识别 + 意图准确率。

用法：
  python scripts/eval.py            # 全部
  python scripts/eval.py --no-llm   # 只跑合规（不调用模型，秒出）
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import agent, compliance  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "out"


def load_testset():
    return json.loads((DATA / "testset.json").read_text(encoding="utf-8"))


def pct(a, b):
    return round(100.0 * a / b, 1) if b else 0.0


def eval_compliance(ts):
    report = {}

    # --- 红线：应被识别（block 或 rewrite），判 pass 才算漏杀 ---
    rows = []
    for case in ts["redline"]:
        ev = compliance.evaluate(case["text"], case["market"], case["category"])
        ok = ev["verdict"] != "pass"
        strict = ev["verdict"] == "block"
        rows.append({"id": case["id"], "text": case["text"], "expect": "block",
                     "got": ev["verdict"], "level": ev["level"],
                     "clauses": ev["clauses"], "ok": ok, "strict_block": strict, "why": case["why"]})
    miss = sum(1 for r in rows if not r["ok"])
    strict_n = sum(1 for r in rows if r["strict_block"])
    report["redline"] = {"total": len(rows), "missed": miss,
                         "miss_rate": pct(miss, len(rows)),
                         "strict_block": strict_n,
                         "strict_block_rate": pct(strict_n, len(rows)),
                         "rows": rows}

    # --- 陷阱：应 pass ---
    rows = []
    for case in ts["trap"]:
        ev = compliance.evaluate(case["text"], case["market"], case["category"])
        ok = ev["verdict"] == "pass"
        rows.append({"id": case["id"], "text": case["text"], "expect": "pass",
                     "got": ev["verdict"], "level": ev["level"],
                     "clauses": ev["clauses"], "ok": ok, "why": case["why"]})
    false_pos = sum(1 for r in rows if not r["ok"])
    report["trap"] = {"total": len(rows), "false_positive": false_pos,
                      "false_positive_rate": pct(false_pos, len(rows)), "rows": rows}

    # --- 擦边：应 rewrite（pass 算漏，block 也算命中但级别偏高）---
    rows = []
    for case in ts["grey"]:
        ev = compliance.evaluate(case["text"], case["market"], case["category"])
        ok = ev["verdict"] in ("rewrite", "block")
        rows.append({"id": case["id"], "text": case["text"], "expect": "rewrite",
                     "got": ev["verdict"], "level": ev["level"],
                     "clauses": ev["clauses"], "ok": ok, "why": case["why"]})
    hit = sum(1 for r in rows if r["ok"])
    report["grey"] = {"total": len(rows), "hit": hit,
                      "hit_rate": pct(hit, len(rows)), "rows": rows}

    # --- 汇总 ---
    report["summary"] = {
        "红线漏杀率": f"{report['redline']['miss_rate']}%  (目标 ≤5%)",
        "红线严格拦截率": f"{report['redline']['strict_block_rate']}%  (判为 block 的比例)",
        "误杀率": f"{report['trap']['false_positive_rate']}%  (目标 ≤10%)",
        "擦边识别率": f"{report['grey']['hit_rate']}%  (目标 ≥80%)",
    }
    return report


def eval_intent(ts, limit=None):
    cases = ts["intent"][:limit] if limit else ts["intent"]
    rows = []
    t0 = time.perf_counter()
    for case in cases:
        got = agent.classify(case["text"])
        pred = got.get("intent")
        ok = pred == case["expect"]
        rows.append({"id": case["id"], "text": case["text"], "expect": case["expect"],
                     "got": pred, "flags": got.get("flags"),
                     "emotion": got.get("emotion"), "ok": ok})
    correct = sum(1 for r in rows if r["ok"])
    return {
        "total": len(rows), "correct": correct,
        "accuracy": pct(correct, len(rows)),
        "seconds": round(time.perf_counter() - t0, 1),
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true", help="只跑合规，不调模型")
    ap.add_argument("--intent-limit", type=int, default=None)
    args = ap.parse_args()

    ts = load_testset()
    OUT.mkdir(exist_ok=True)

    print("=== 合规 ===")
    comp = eval_compliance(ts)
    for k, v in comp["summary"].items():
        print(f"  {k}: {v}")

    result = {"compliance": comp}

    if not args.no_llm:
        print("=== 意图 ===")
        intent = eval_intent(ts, args.intent_limit)
        print(f"  准确率: {intent['accuracy']}%  ({intent['correct']}/{intent['total']}, {intent['seconds']}s)")
        result["intent"] = intent

    path = OUT / "eval_result.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwritten: {path}")


if __name__ == "__main__":
    main()
