# -*- coding: utf-8 -*-
"""语义兜底专项验证：用规则肯定覆盖不到的表述，看语义层能否补上。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import compliance, semantic  # noqa: E402

# 故意避开规则里所有 patterns 的原话
CASES = [
    # 应拦：全新措辞的违规
    ("N01", "Our tea will make your blood sugar drop naturally.", "US", "supplement", False),
    ("N02", "You will never see a wrinkle again after two weeks.", "EU", "cosmetic", False),
    ("N03", "这款产品能让你的斑完全消失，不用去医院。", "CN", "cosmetic", False),
    ("N04", "It works for everyone, no matter how severe the condition.", "US", "cosmetic", False),
    ("N05", "We ship by Friday, no excuses.", "EU", "cosmetic", False),
    # 应放：全新措辞但合规
    ("N06", "This balm is not designed to address any medical condition.", "US", "cosmetic", True),
    ("N07", "我们无法保证具体到货时间，请以物流信息为准。", "CN", "cosmetic", True),
    ("N08", "If irritation occurs, stop using and seek medical advice.", "EU", "cosmetic", True),
    ("N09", "We do not offer compensation beyond the published policy.", "US", "cosmetic", True),
    ("N10", "本产品不涉及任何疾病预防或治疗用途。", "CN", "cosmetic", True),
]


def judge(text, market, cat, use_sem):
    ev = compliance.evaluate(text, market, cat)
    if not use_sem:
        return ev
    if ev["verdict"] == "pass" and semantic.should_check(text):
        sem = semantic.check(text, market, cat)
        if sem and sem["verdict"] != "pass":
            return sem
    return ev


lines = []
base_ok = sem_ok = 0
for cid, text, market, cat, expect_pass in CASES:
    ev = judge(text, market, cat, False)
    ok1 = (ev["verdict"] == "pass") if expect_pass else (ev["verdict"] != "pass")
    ev2 = judge(text, market, cat, True)
    ok2 = (ev2["verdict"] == "pass") if expect_pass else (ev2["verdict"] != "pass")
    base_ok += ok1
    sem_ok += ok2
    flag = "  <-- 语义层补上" if (not ok1 and ok2) else ("  <-- 语义层弄错" if (ok1 and not ok2) else "")
    lines.append(f"{cid} 期望={'放行' if expect_pass else '拦截'}")
    lines.append(f"   规则: {ev['verdict']:7s} {ev.get('reason','')[:34]}")
    lines.append(f"   语义: {ev2['verdict']:7s} {ev2.get('reason','')[:34]}{flag}")

lines.append("")
lines.append(f"规则层: {base_ok}/{len(CASES)}   规则+语义: {sem_ok}/{len(CASES)}")
out = "\n".join(lines)
(ROOT / "out" / "semantic_gain.txt").write_text(out, encoding="utf-8")
print(out)
