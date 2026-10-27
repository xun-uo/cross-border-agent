# -*- coding: utf-8 -*-
"""留出集验证：15 条未参与调参的样本，用于估计真实泛化水平。

不修改任何规则，只跑一次并如实报告。这些样本刻意避开现有 patterns 的原话。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import compliance  # noqa: E402

CASES = [
    # ---- 红线（应被识别，最好 block）----
    ("H01", "This pill is proven to reverse type 2 diabetes.", "US", "supplement", "block", "疾病宣称（表述全新）"),
    ("H02", "Our lotion heals burns within two days.", "US", "cosmetic", "block", "化妆品治伤（burns 不在疾病表）"),
    ("H03", "Buy now, the price doubles tomorrow.", "EU", "cosmetic", "rewrite", "虚假紧迫（price doubles）"),
    ("H04", "We promise a full refund before any inspection.", "US", "cosmetic", "block", "超权限退款承诺"),
    ("H05", "本品抗癌，长期服用可防癌。", "CN", "supplement", "block", "食品宣称防癌", ),
    # ---- 陷阱（应放行）----
    ("H06", "This product is not a medicine and is not intended for treating illness.", "US", "cosmetic", "pass", "双重否定式"),
    ("H07", "我们不做任何疗效承诺。", "CN", "cosmetic", "pass", "否定式"),
    ("H08", "We cannot promise same-day shipping.", "US", "cosmetic", "pass", "否定式"),
    ("H09", "This supplement does not prevent or cure any disease. This statement has not been evaluated by the FDA.", "US", "supplement", "pass", "否定式+免责"),
    ("H10", "效果因人而异，不保证见效。", "CN", "cosmetic", "pass", "否定式"),
    # ---- 擦边（应被识别为 rewrite）----
    ("H11", "This cream visibly reduces fine lines.", "EU", "cosmetic", "rewrite", "功效暗示"),
    ("H12", "Clinically proven to reduce breakouts.", "EU", "cosmetic", "rewrite", "临床证明"),
    ("H13", "Only today: buy one get one free.", "EU", "cosmetic", "rewrite", "虚假紧迫（Only today）"),
    ("H14", "Our formula works faster than any competitor.", "US", "cosmetic", "rewrite", "贬低竞品（faster than any）"),
    ("H15", "7 天见效，无效退款。", "CN", "cosmetic", "rewrite", "效果承诺"),
]

groups = {"redline": [], "trap": [], "grey": []}
for cid, text, market, category, expect, why in CASES:
    ev = compliance.evaluate(text, market, category)
    if expect == "pass":
        ok = ev["verdict"] == "pass"
        g = "trap"
    else:
        ok = ev["verdict"] != "pass"
        g = "redline" if expect == "block" else "grey"
    groups[g].append({"id": cid, "text": text, "market": market, "category": category,
                      "expect": expect, "got": ev["verdict"], "level": ev["level"],
                      "clauses": ev["clauses"], "ok": ok, "why": why})

lines = ["=== 留出集（未参与调参）==="]
for g in ("redline", "trap", "grey"):
    rows = groups[g]
    fails = [r for r in rows if not r["ok"]]
    lines.append(f"\n[{g}] {len(rows) - len(fails)}/{len(rows)} 通过")
    for r in fails:
        lines.append(f"  FAIL {r['id']} expect={r['expect']} got={r['got']} ({r['level']}) | {r['text'][:70]}")

total = sum(len(v) for v in groups.values())
ok_total = sum(1 for v in groups.values() for r in v if r["ok"])
lines.append(f"\n总通过率: {round(100.0 * ok_total / total, 1)}% ({ok_total}/{total})")
out = ROOT / "out" / "holdout.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
