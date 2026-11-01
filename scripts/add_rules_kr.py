# -*- coding: utf-8 -*-
"""补韩国膳食补充剂规则 2 条。

依据（2026-11-01 核对）：
- 《食品等的标示·广告相关法律》第 8 条 — 不当标示·广告的禁止（总则，四类：虚假夸大/欺骗/不当比较/诽谤）
- 同法施行令 [별표 1] 第 1 号 —「질병의 예방·치료에 효능·효과가 있거나
  의약품으로 오인·혼동할 우려가 있는 내용」= 禁止清单本体
- 同法第 4 条要求健康功能食品必须标示「질병의 예방 및 치료를 위한 의약품이 아니라는
  내용의 표현」——此句直接从 MFDS《건강기능식품의 표시기준》(2022.11) 提取，
  因此「宣称能治病即违规」有正反两面依据。

两条按同一条款的两个落点拆：治疗类宣称 / 预防与生理指标类宣称。
不动「의약품」单独做 pattern（「의약품이 아닙니다」是法定合规表述，会误杀）。
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NEW = [
    {
        "id": "KR-SUP-8-1",
        "market": "KR",
        "category": "supplement",
        "level": "L1",
        "action": "block",
        "clause": "식품 등의 표시·광고에 관한 법률 제8조 · 시행령 별표1 제1호",
        "trigger": "健康功能食品宣称疾病治疗、治愈功效",
        "patterns": ["치료", "완치", "항암", "항암효과", "비만치료", "질병치료",
                     "치료효과", "치유"],
        "patterns_en": ["cure", "cures", "anti-cancer", "anticancer",
                        "treats disease", "disease treatment", "heals"],
        "exempt": ["의약품이 아닙니다", "의약품이 아니라는", "치료 목적이 아닌",
                   "not intended to treat", "not a medicine", "не является лекарством"],
    },
    {
        "id": "KR-SUP-8-2",
        "market": "KR",
        "category": "supplement",
        "level": "L1",
        "action": "block",
        "clause": "식품 등의 표시·광고에 관한 법률 시행령 별표1 제1호",
        "trigger": "健康功能食品宣称疾病预防或直接干预生理指标",
        "patterns": ["질병예방", "질병 예방", "예방효과", "혈압강하", "혈당조절",
                     "혈당 조절", "당뇨개선", "당뇨 개선", "염증완화", "염증 완화",
                     "콜레스테롤 저하", "면역력 치료"],
        "patterns_en": ["prevents disease", "lowers blood pressure",
                        "blood sugar control", "treats diabetes",
                        "reduces inflammation", "lowers cholesterol"],
        "exempt": ["도움을 줄 수 있", "도움이 될 수 있", "도움을 줄 수 있다는",
                   "may help", "helps maintain", "immune support"],
    },
]

p = Path(r"D:\跨境智服\data\rules.json")
rules = json.loads(p.read_text(encoding="utf-8"))
have = {r["id"] for r in rules}
added = 0
for r in NEW:
    if r["id"] not in have:
        rules.append(r)
        added += 1
p.write_text(json.dumps(rules, ensure_ascii=False, indent=1), encoding="utf-8")
print("规则：新增 %d，当前共 %d" % (added, len(rules)))
