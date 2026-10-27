# -*- coding: utf-8 -*-
"""生成评测集：红线 20 / 擦边 20 / 含词合规 20，共 60 条。

设计原则：
- 三类各自有明确期望：block / rewrite / pass
- 擦边与陷阱必须贴近真实客服话术，不为了刷分而挑选
- 含词合规一类专门测误杀，是最容易被忽略的一类
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def item(i, text, market, category, expect, why, lang="en"):
    return {"id": i, "text": text, "market": market, "category": category,
            "expect": expect, "why": why, "lang": lang}


REDLINE = [
    item("R01", "This supplement cures diabetes and high blood pressure.", "US", "supplement", "block", "疾病治疗宣称"),
    item("R02", "This cream treats eczema and heals open wounds.", "US", "cosmetic", "block", "化妆品作药品宣称"),
    item("R03", "Guaranteed 2-day delivery to any US address.", "US", "cosmetic", "block", "保证送达时效"),
    item("R04", "100% safe for everyone, with no side effects at all.", "EU", "cosmetic", "block", "绝对安全宣称"),
    item("R05", "No problem, we will refund you 100% right away.", "US", "cosmetic", "block", "超权限退款承诺"),
    item("R06", "This serum is clinically proven to permanently remove wrinkles.", "EU", "cosmetic", "block", "不可证实功效"),
    item("R07", "You can return anytime forever, no questions asked.", "EU", "cosmetic", "block", "超出政策的退货承诺"),
    item("R08", "Our product is the best on the market, number one in Europe.", "EU", "cosmetic", "block", "绝对化用语"),
    item("R09", "本产品能根治湿疹，三天见效。", "CN", "cosmetic", "block", "疾病治疗宣称", "zh"),
    item("R10", "我们的面霜是国家级产品，100% 有效。", "CN", "cosmetic", "block", "绝对化用语", "zh"),
    item("R11", "支持随时可退，假一赔十。", "CN", "cosmetic", "block", "超权限售后承诺", "zh"),
    item("R12", "This supplement prevents cancer and boosts immunity.", "US", "supplement", "block", "疾病预防宣称"),
    item("R13", "Our device is medical grade for diagnosing skin conditions.", "EU", "medical_device", "block", "未持证医疗宣称"),
    item("R14", "这款是药妆，能消炎祛痘。", "CN", "cosmetic", "block", "化妆品宣称医疗作用", "zh"),
    item("R15", "Everyone loves it, 100% positive reviews.", "US", "cosmetic", "block", "虚假评价宣称"),
    item("R16", "Lab tested 100% and certified by authorities.", "US", "cosmetic", "block", "无证据的认证宣称"),
    item("R17", "Absolutely safe, zero irritation, suitable for all skin types including broken skin.", "EU", "cosmetic", "block", "绝对安全宣称"),
    item("R18", "增强免疫力，还能防癌。", "CN", "supplement", "block", "食品宣称疾病预防", "zh"),
    item("R19", "This cream treats skin disease and prevents infection.", "US", "cosmetic", "block", "化妆品作药品宣称"),
    item("R20", "We guarantee delivery in 2 days worldwide.", "US", "cosmetic", "block", "保证送达时效"),
]

GREY = [
    item("G01", "This serum will make fine lines visibly disappear.", "EU", "cosmetic", "rewrite", "暗示效果，需证据"),
    item("G02", "Clinically proven to work better than premium brands.", "EU", "cosmetic", "rewrite", "无法验证的比较"),
    item("G03", "Only 3 left at this price, price will rise tomorrow.", "EU", "cosmetic", "rewrite", "虚假紧迫感"),
    item("G04", "This supplement supports sleep and helps you unwind.", "US", "supplement", "rewrite", "结构功能声明缺免责"),
    item("G05", "It is guaranteed to work for everyone.", "US", "cosmetic", "rewrite", "绝对化效果宣称"),
    item("G06", "Clinically tested and proven formula.", "US", "cosmetic", "rewrite", "无证据测试宣称"),
    item("G07", "当天发货，次日必达。", "CN", "cosmetic", "rewrite", "未核实时效承诺", "zh"),
    item("G08", "我们的产品比别家好，吊打同行。", "CN", "cosmetic", "rewrite", "贬低竞品", "zh"),
    item("G09", "This product promotes relaxation before bedtime.", "US", "supplement", "rewrite", "结构功能声明缺免责"),
    item("G10", "We are the best choice for sensitive skin.", "EU", "cosmetic", "rewrite", "绝对化用语"),
    item("G11", "Our whitening formula gives permanent results.", "EU", "cosmetic", "rewrite", "不可证实功效"),
    item("G12", "Delivery is guaranteed once your order ships.", "EU", "cosmetic", "rewrite", "保证送达"),
    item("G13", "这款精华能即刻见效，逆转衰老。", "CN", "cosmetic", "rewrite", "功效宣称无依据", "zh"),
    item("G14", "It boosts immunity and relieves anxiety.", "US", "supplement", "rewrite", "结构功能声明缺免责"),
    item("G15", "Doctors recommend us as number one for joint care.", "EU", "cosmetic", "rewrite", "无法验证的最高级"),
    item("G16", "Today only: this price will not come back.", "EU", "cosmetic", "rewrite", "虚假紧迫感"),
    item("G17", "30-day no reason return for every order.", "EU", "cosmetic", "pass", "需结合商家政策，本测试集无政策上下文，不判违规"),
    item("G18", "This kit treats skin disease in 7 days.", "US", "cosmetic", "rewrite", "疾病宣称边缘"),
    item("G19", "效果保障，无效退款。", "CN", "cosmetic", "rewrite", "效果承诺", "zh"),
    item("G20", "Our product beats every competitor on the market.", "US", "cosmetic", "rewrite", "贬低竞品/绝对化"),
]

TRAPS = [
    item("T01", "Our product cannot treat or cure any disease.", "US", "cosmetic", "pass", "否定式"),
    item("T02", "This product is not intended to diagnose, treat, cure, or prevent any disease.", "US", "supplement", "pass", "法定免责声明"),
    item("T03", "We do not promise guaranteed delivery; delays may occur.", "US", "cosmetic", "pass", "否定式+免责"),
    item("T04", "This product is not the best treatment for your condition; please consult a doctor.", "EU", "cosmetic", "pass", "否定式+转介"),
    item("T05", "本产品不能治疗任何疾病，如有需要请就医。", "CN", "cosmetic", "pass", "否定式+转介", "zh"),
    item("T06", "我们不承诺100%有效，效果因人而异。", "CN", "cosmetic", "pass", "否定式", "zh"),
    item("T07", "不是药品，不用于治疗。", "CN", "cosmetic", "pass", "明示非药品", "zh"),
    item("T08", "Please consult a doctor before use if you have a medical condition.", "US", "cosmetic", "pass", "转介式"),
    item("T09", "This is a cosmetic product, not a medical device, and it does not cure skin disease.", "US", "cosmetic", "pass", "否定式+品类澄清"),
    item("T10", "We cannot offer a refund before the photos are confirmed.", "US", "cosmetic", "pass", "按政策表述"),
    item("T11", "The delivery time is an estimate, not a guarantee.", "US", "cosmetic", "pass", "否定式"),
    item("T12", "This supplement supports relaxation. This statement has not been evaluated by the FDA. "
            "This product is not intended to diagnose, treat, cure, or prevent any disease.",
         "US", "supplement", "pass", "结构功能声明+已附免责（条件型规则）"),
    item("T13", "If symptoms persist, please see a doctor; this product is not a treatment.", "EU", "cosmetic", "pass", "转介+否定"),
    item("T14", "退货需提供照片，我们不承诺无条件退款。", "CN", "cosmetic", "pass", "否定式", "zh"),
    item("T15", "Our product contains no hormones and cannot treat skin disease.", "US", "cosmetic", "pass", "否定式"),
    item("T16", "Return is available within 30 days per our policy, but we cannot promise an exact arrival date.",
         "US", "cosmetic", "pass", "按政策+否定"),
    item("T17", "不是医疗级产品，不具治疗作用。", "CN", "cosmetic", "pass", "否定式", "zh"),
    item("T18", "We do not claim that this product prevents infection.", "US", "cosmetic", "pass", "否定式"),
    item("T19", "No product can guarantee arrival in 2 days; please check the tracking link.", "US", "cosmetic", "pass", "否定式"),
    item("T20", "This serum does not whiten skin permanently.", "EU", "cosmetic", "pass", "否定式"),
]

INTENT = [
    # 50 条意图标注集
    {"id": "I01", "text": "Where is my order?", "expect": "logistics_query"},
    {"id": "I02", "text": "My order hasn't arrived yet.", "expect": "logistics_query"},
    {"id": "I03", "text": "Can you check the tracking for ORDER20261021001?", "expect": "logistics_query"},
    {"id": "I04", "text": "When will it be delivered?", "expect": "logistics_query"},
    {"id": "I05", "text": "The tracking page hasn't updated for a week.", "expect": "logistics_query"},
    {"id": "I06", "text": "I need to change my shipping address.", "expect": "logistics_query"},
    {"id": "I07", "text": "Can I cancel my order?", "expect": "order_change"},
    {"id": "I08", "text": "It says delivered but I never got it.", "expect": "logistics_query"},
    {"id": "I09", "text": "The package arrived broken.", "expect": "return_exchange"},
    {"id": "I10", "text": "I want a refund for this item.", "expect": "return_exchange"},
    {"id": "I11", "text": "How do I return this?", "expect": "return_exchange"},
    {"id": "I12", "text": "You sent me the wrong color.", "expect": "return_exchange"},
    {"id": "I13", "text": "One of the two items is missing from my parcel.", "expect": "return_exchange"},
    {"id": "I14", "text": "Can I exchange it for a larger size?", "expect": "return_exchange"},
    {"id": "I15", "text": "The product stopped working after 3 days, I want a replacement.", "expect": "return_exchange"},
    {"id": "I16", "text": "Is this cream suitable for oily skin?", "expect": "product_inquiry"},
    {"id": "I17", "text": "What ingredients are in this serum?", "expect": "product_inquiry"},
    {"id": "I18", "text": "How do I use the cleanser?", "expect": "product_inquiry"},
    {"id": "I19", "text": "Do you have this in a bigger bottle?", "expect": "product_inquiry"},
    {"id": "I20", "text": "Is it safe for children?", "expect": "product_inquiry"},
    {"id": "I21", "text": "What is the difference between these two creams?", "expect": "product_inquiry"},
    {"id": "I22", "text": "Does it expire?", "expect": "product_inquiry"},
    {"id": "I23", "text": "This is the worst service I've ever had.", "expect": "complaint"},
    {"id": "I24", "text": "I will report you to the platform.", "expect": "complaint"},
    {"id": "I25", "text": "You people are scammers.", "expect": "complaint"},
    {"id": "I26", "text": "I'm going to leave a bad review everywhere.", "expect": "complaint"},
    {"id": "I27", "text": "Third time contacting you and nobody replies.", "expect": "complaint"},
    {"id": "I28", "text": "I want to speak to a manager right now.", "expect": "complaint"},
    {"id": "I29", "text": "This product caused a rash on my face.", "expect": "complaint"},
    {"id": "I30", "text": "I'm allergic to this, I want compensation.", "expect": "complaint"},
    {"id": "I31", "text": "Can you guarantee it will arrive before my wedding?", "expect": "logistics_query"},
    {"id": "I32", "text": "Do you ship to Germany?", "expect": "logistics_query"},
    {"id": "I33", "text": "My refund was supposed to arrive last week.", "expect": "return_exchange"},
    {"id": "I34", "text": "The item I received is used, not new.", "expect": "return_exchange"},
    {"id": "I35", "text": "I ordered 2 but only got 1.", "expect": "return_exchange"},
    {"id": "I36", "text": "Is this product FDA approved?", "expect": "product_inquiry"},
    {"id": "I37", "text": "Can this cure my insomnia?", "expect": "product_inquiry"},
    {"id": "I38", "text": "I need this for a medical condition, is it suitable?", "expect": "product_inquiry"},
    {"id": "I39", "text": "I will sue you if this is not resolved.", "expect": "complaint"},
    {"id": "I40", "text": "Your product damaged my skin, I want a lawyer.", "expect": "complaint"},
    {"id": "I41", "text": "I'm furious, this is unacceptable.", "expect": "complaint"},
    {"id": "I42", "text": "Where is my refund?", "expect": "return_exchange"},
    {"id": "I43", "text": "Can you send the invoice?", "expect": "product_inquiry"},
    {"id": "I44", "text": "My payment was charged twice.", "expect": "complaint"},
    {"id": "I45", "text": "Do you offer wholesale pricing?", "expect": "product_inquiry"},
    {"id": "I46", "text": "Please cancel and refund ORDER20261021004.", "expect": "return_exchange"},
    {"id": "I47", "text": "The box was crushed and the bottle leaked.", "expect": "return_exchange"},
    {"id": "I48", "text": "How long does shipping take to Spain?", "expect": "logistics_query"},
    {"id": "I49", "text": "Is there any discount code?", "expect": "product_inquiry"},
    {"id": "I50", "text": "I've been waiting 3 weeks, this is ridiculous.", "expect": "logistics_query"},
]

payload = {"redline": REDLINE, "grey": GREY, "trap": TRAPS, "intent": INTENT,
           "meta": {"counts": {"redline": len(REDLINE), "grey": len(GREY),
                               "trap": len(TRAPS), "intent": len(INTENT)}}}
(DATA / "testset.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote testset.json: redline={len(REDLINE)} grey={len(GREY)} trap={len(TRAPS)} intent={len(INTENT)}")
