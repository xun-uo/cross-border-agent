# -*- coding: utf-8 -*-
"""补医疗器械规则（中国 2 条 + 美国 1 条），条款均已核对原文。

- 中国：广东省市场监管局答问库确认《广告法》第十六条「不得含有表示功效、安全性的
  断言或者保证」；同条第一款第（二）项为「说明治愈率或者有效率」。
- 美国：21 CFR 801.109(b)(1) 原文要求处方器械标签标注 "Rx only" 或
  "Caution: Federal law restricts this device to sale by or on the order of a physician"，
  且只能凭执业医师处方销售 —— 属条件型，用 L2/rewrite，不是一律拦截。

韩国两条没有拿到可靠韩文原文，留空，等队友。
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

NEW = [
    {
        "id": "CN-MD-16-1",
        "market": "CN",
        "category": "medical_device",
        "level": "L1",
        "action": "block",
        "clause": "广告法 第十六条第一款第（一）项",
        "trigger": "医疗器械宣称功效或安全性的断言、保证",
        "patterns": ["绝对有效", "百分百有效", "百分之百有效", "保证治好",
                     "药到病除", "包治百病", "绝对安全", "零风险", "无任何副作用"],
        "patterns_en": ["guaranteed to cure", "100% effective", "absolutely safe",
                        "zero risk", "no side effects at all", "certain cure"],
        "exempt": ["无法保证", "不能保证", "不保证", "no guarantee",
                   "not guaranteed", "cannot guarantee"],
    },
    {
        "id": "CN-MD-16-2",
        "market": "CN",
        "category": "medical_device",
        "level": "L1",
        "action": "block",
        "clause": "广告法 第十六条第一款第（二）项",
        "trigger": "医疗器械宣称治愈率、有效率、成功率等疗效数据",
        "patterns": ["治愈率", "有效率", "成功率", "好转率", "显效率",
                     "有效率高达", "治愈率高达"],
        "patterns_en": ["cure rate", "effective rate", "success rate", "efficacy rate"],
        "exempt": [],
    },
    {
        "id": "US-MD-801-109",
        "market": "US",
        "category": "medical_device",
        "level": "L2",
        "action": "rewrite",
        "clause": "21 CFR 801.109(b)(1)",
        "trigger": "处方类医疗器械宣称无需处方即可购买或使用",
        "patterns": ["无需处方", "不用处方", "免处方", "直接购买使用", "随便买"],
        "patterns_en": ["no prescription needed", "no prescription required",
                        "available without a prescription", "buy without prescription"],
        "exempt": ["凭处方", "需处方", "遵医嘱", "prescription required",
                   "by prescription only", "rx only"],
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
