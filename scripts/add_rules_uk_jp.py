# -*- coding: utf-8 -*-
"""补英国、日本各 5 条规则。

依据（2026-11-01 第四轮调研，条款号与官方域名均核对过）：
日本：
- 薬機法第2条第3項 + 厚労省通知（薬食発0721第1号）附表1 —— 化妆品只能宣称法定 56 项功效
- 薬機法第68条 —— 虚假夸大广告禁止
- 景品表示法第5条第1項第1号・第2号 —— 優良誤認・有利誤認
- 食品表示法 / 機能性表示食品制度 —— 保健機能食品不得宣称治疗预防疾病
- 特定商取引法第15条の2 —— 通信販売返品特約的表示义务
英国：
- CAP Code Rule 12.1 + Human Medicines Regulations 2012 —— 化妆品不得作医疗宣称
- CAP Code Rule 3.39/3.40 —— 绝对化/最高级须有证据
- CAP Code Rule 15 + Nutrition and Health Claims (England) Regulations 2007 + GB NHC Register
- Consumer Contracts (Information, Cancellation and Additional Charges) Regulations 2013 reg.29-34 —— 14 天冷静期
- Medical Devices Regulations 2002 (SI 2002/618) + UKCA/MHRA —— 非医疗器械不得宣称医疗用途

注意：日本市场的 patterns 用日文原词，因为合规匹配是子串匹配，
日文假名不会出现在中文句子里，混用反而互相干扰。
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NEW = [
    # ---------------- 日本 ----------------
    {
        "id": "JP-COS-2-3",
        "market": "JP",
        "category": "cosmetic",
        "level": "L1",
        "action": "block",
        "clause": "薬機法 第2条第3項；厚労省通知 薬食発0721第1号 附表1",
        "trigger": "化妆品宣称超出法定 56 项功效范围（暗示医疗效果）",
        "patterns": ["シミを消す", "シミが消える", "ニキビを治す", "ニキビが治る",
                     "炎症を抑える", "毛穴を根本から改善", "肌を再生", "若返る",
                     "アトピー改善", "アレルギー改善"],
        "patterns_en": ["removes spots", "cures acne", "treats inflammation",
                        "regenerates skin", "repairs atopic skin"],
        "exempt": ["医薬部外品", "医薬品ではありません", "not a medicine"],
    },
    {
        "id": "JP-ADL-68",
        "market": "JP",
        "category": "*",
        "level": "L1",
        "action": "block",
        "clause": "薬機法 第68条（虚偽又は誇大な記事の禁止）",
        "trigger": "对功效作虚假或夸大的绝对化宣称",
        "patterns": ["必ず治る", "絶対に治る", "完全に治る", "100%治る",
                     "絶対痩せる", "必ず痩せる", "副作用なし", "完全無欠"],
        "patterns_en": ["guaranteed cure", "completely cures", "100% cure",
                        "no side effects", "definitely works"],
        "exempt": ["個人の感想", "効果には個人差", "individual results"],
    },
    {
        "id": "JP-PROMO-5",
        "market": "JP",
        "category": "*",
        "level": "L2",
        "action": "rewrite",
        "clause": "景品表示法 第5条第1項第1号・第2号（優良誤認・有利誤認）",
        "trigger": "绝对化、最高级或双价对比等可能造成误解的表述",
        "patterns": ["日本一", "世界一", "業界No.1", "最高品質", "最安値",
                     "通常価格の半額", "今だけ半額"],
        "patterns_en": ["no.1 in japan", "world's best", "industry leader",
                        "half price today only"],
        "exempt": ["調査に基づく", "出典", "based on survey"],
    },
    {
        "id": "JP-SUP-3",
        "market": "JP",
        "category": "supplement",
        "level": "L1",
        "action": "block",
        "clause": "食品表示法；機能性表示食品制度；健康増進法",
        "trigger": "保健機能食品宣称疾病治疗、预防功效",
        "patterns": ["糖尿病を治す", "血圧を下げる", "血糖値を下げる",
                     "がんを治す", "病気を防ぐ", "病院いらず", "脂肪肝を解消"],
        "patterns_en": ["cures diabetes", "lowers blood pressure",
                        "prevents cancer", "prevents disease"],
        "exempt": ["疾病の予防・治療を目的としたものではありません", "not intended to"],
    },
    {
        "id": "JP-RETURN-15-2",
        "market": "JP",
        "category": "*",
        "level": "L2",
        "action": "rewrite",
        "clause": "特定商取引法 第15条の2（通信販売の返品特約の表示）",
        "trigger": "通信販売中单方面排除或限制法定退货权",
        "patterns": ["返品不可", "返品・交換不可", "一切返品できません",
                     "返品は受け付けません", "交換はできません"],
        "patterns_en": ["no returns", "no exchange", "returns not accepted"],
        "exempt": ["返品特約", "8日以内", "未使用に限り"],
    },
    # ---------------- 英国 ----------------
    {
        "id": "UK-MED-12",
        "market": "UK",
        "category": "cosmetic",
        "level": "L1",
        "action": "block",
        "clause": "CAP Code Rule 12.1；Human Medicines Regulations 2012",
        "trigger": "化妆品宣称医疗功效（治疗、治愈、预防疾病）",
        "patterns": ["cures acne", "cure eczema", "treats eczema", "reverses psoriasis",
                     "treats inflammation", "clinically proven to heal",
                     "heals wounds", "treats rosacea"],
        "patterns_en": ["cures acne", "treats eczema", "reverses psoriasis",
                        "anti-inflammatory cream", "heals wounds"],
        "exempt": ["not intended to treat", "cosmetic claim", "does not treat"],
    },
    {
        "id": "UK-ADL-3",
        "market": "UK",
        "category": "*",
        "level": "L2",
        "action": "rewrite",
        "clause": "CAP Code Rule 3.39 / 3.40（绝对化、最高级宣称须有证据）",
        "trigger": "使用绝对化或无法客观验证的最高级表述",
        "patterns": ["the best", "no.1", "number one", "guaranteed results",
                     "100% effective", "unparalleled", "world's leading"],
        "patterns_en": ["the best", "no.1", "number one", "guaranteed",
                        "100% effective", "unparalleled"],
        "exempt": ["award-winning", "based on survey", "compared to"],
    },
    {
        "id": "UK-SUP-15",
        "market": "UK",
        "category": "supplement",
        "level": "L1",
        "action": "block",
        "clause": "CAP Code Rule 15；Nutrition and Health Claims (England) Regulations 2007；GB NHC Register",
        "trigger": "食品补充剂健康声称未获 GB NHC Register 授权或宣称治病",
        "patterns": ["boosts immunity against colds", "detoxifies the liver",
                     "cures insomnia", "treats insomnia", "balances hormones",
                     "repairs gut lining", "prevents illness"],
        "patterns_en": ["boosts immunity against", "detoxifies", "cures insomnia",
                        "balances hormones", "repairs gut"],
        "exempt": ["authorised claim", "gb nhc register", "not intended to treat"],
    },
    {
        "id": "UK-RET-29",
        "market": "UK",
        "category": "*",
        "level": "L2",
        "action": "rewrite",
        "clause": "Consumer Contracts (Information, Cancellation and Additional Charges) Regulations 2013 reg. 29-34",
        "trigger": "单方面排除或限制法定 14 天冷静期退货权",
        "patterns": ["no returns", "all sales final", "returns only if faulty",
                     "custom items always non-returnable", "non-refundable",
                     "no refund for online orders"],
        "patterns_en": ["no returns", "all sales final", "returns only if faulty",
                        "non-refundable"],
        "exempt": ["14 days", "cooling-off period", "statutory right"],
    },
    {
        "id": "UK-MDR-2002",
        "market": "UK",
        "category": "medical_device",
        "level": "L1",
        "action": "block",
        "clause": "Medical Devices Regulations 2002 (SI 2002/618)；UKCA / MHRA 要求",
        "trigger": "非医疗器械被宣称医疗用途，或器械宣称未获批准的诊断治疗功能",
        "patterns": ["medical-grade treatment device", "clinically certified to cure",
                     "mhra-approved device", "hospital-grade laser therapy",
                     "diagnoses skin disease", "cures disease"],
        "patterns_en": ["medical-grade treatment", "clinically certified to cure",
                        "mhra-approved", "diagnoses", "cures disease"],
        "exempt": ["ukca marked", "registered device", "not intended to diagnose"],
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
import collections
print("市场分布:", dict(collections.Counter(r["market"] for r in rules)))
