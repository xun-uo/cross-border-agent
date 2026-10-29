# -*- coding: utf-8 -*-
"""对比评测：纯规则层 vs 规则 + 语义兜底层。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import compliance, semantic  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "out"


def judge(draft, market, category, use_semantic):
    ev = compliance.evaluate(draft, market, category)
    if not use_semantic:
        return ev
    if ev["verdict"] == "pass" and semantic.should_check(draft):
        sem = semantic.check(draft, market, category)
        if sem and sem["verdict"] != "pass":
            return sem
    return ev


def run_set(name, items, expect_pass, use_semantic):
    rows = []
    for it in items:
        ev = judge(it["text"], it["market"], it["category"], use_semantic)
        ok = (ev["verdict"] == "pass") if expect_pass else (ev["verdict"] != "pass")
        rows.append({"id": it["id"], "text": it["text"], "got": ev["verdict"],
                     "level": ev["level"], "reason": ev.get("reason", ""), "ok": ok})
    good = sum(1 for r in rows if r["ok"])
    return {"name": name, "total": len(rows), "ok": good,
            "rate": round(100.0 * good / len(rows), 1) if rows else 0, "rows": rows}


def main():
    ts = json.loads((DATA / "testset.json").read_text(encoding="utf-8"))
    hold = [
        ("H01", "This pill is proven to reverse type 2 diabetes.", "US", "supplement", False),
        ("H02", "Our lotion heals burns within two days.", "US", "cosmetic", False),
        ("H03", "Buy now, the price doubles tomorrow.", "EU", "cosmetic", False),
        ("H04", "We promise a full refund before any inspection.", "US", "cosmetic", False),
        ("H05", "本品抗癌，长期服用可防癌。", "CN", "supplement", False),
        ("H06", "This product is not a medicine and is not intended for treating illness.", "US", "cosmetic", True),
        ("H07", "我们不做任何疗效承诺。", "CN", "cosmetic", True),
        ("H08", "We cannot promise same-day shipping.", "US", "cosmetic", True),
        ("H09", "This supplement does not prevent or cure any disease. This statement has not been evaluated by the FDA.", "US", "supplement", True),
        ("H10", "效果因人而异，不保证见效。", "CN", "cosmetic", True),
        ("H11", "This cream visibly reduces fine lines.", "EU", "cosmetic", False),
        ("H12", "Clinically proven to reduce breakouts.", "EU", "cosmetic", False),
        ("H13", "Only today: buy one get one free.", "EU", "cosmetic", False),
        ("H14", "Our formula works faster than any competitor.", "US", "cosmetic", False),
        ("H15", "7 天见效，无效退款。", "CN", "cosmetic", False),
    ]
    hold_items = [{"id": i, "text": t, "market": m, "category": c} for i, t, m, c, _ in hold]
    hold_expect_pass = {i: p for i, _, _, _, p in hold}

    report = {}

    # 主集红线 + 陷阱
    sets = [("主集·红线", ts["redline"], False), ("主集·陷阱", ts["trap"], True)]

    for label, items, expect_pass in sets:
        base = run_set(label, items, expect_pass, use_semantic=False)
        with_sem = run_set(label, items, expect_pass, use_semantic=True)
        report[label] = {"rule_only": {k: base[k] for k in ("total", "ok", "rate")},
                         "rule_plus_semantic": {k: with_sem[k] for k in ("total", "ok", "rate")},
                         "diffs": [r for r in with_sem["rows"] if not r["ok"]]}

    # 留出集：分违规/合规两组
    red = [it for it in hold_items if not hold_expect_pass[it["id"]]]
    trp = [it for it in hold_items if hold_expect_pass[it["id"]]]
    for label, items, expect_pass in [("留出集·应拦", red, False), ("留出集·应放", trp, True)]:
        base = run_set(label, items, expect_pass, use_semantic=False)
        with_sem = run_set(label, items, expect_pass, use_semantic=True)
        report[label] = {"rule_only": {k: base[k] for k in ("total", "ok", "rate")},
                         "rule_plus_semantic": {k: with_sem[k] for k in ("total", "ok", "rate")},
                         "detail": [{"id": r["id"], "got": r["got"], "ok": r["ok"],
                                     "reason": r["reason"]} for r in with_sem["rows"]]}

    (OUT / "semantic_eval.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    for k, v in report.items():
        ro, rs = v["rule_only"], v["rule_plus_semantic"]
        lines.append(f"{k}: 规则 {ro['ok']}/{ro['total']} ({ro['rate']}%)  ->  "
                     f"规则+语义 {rs['ok']}/{rs['total']} ({rs['rate']}%)")
    if "留出集·应拦" in report:
        lines.append("")
        lines.append("留出集·应拦 明细：")
        for r in report["留出集·应拦"]["detail"]:
            lines.append(f"  {r['id']}: {r['got']} {'OK' if r['ok'] else 'MISS'}  {r['reason'][:40]}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
