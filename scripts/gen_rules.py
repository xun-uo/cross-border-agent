# -*- coding: utf-8 -*-
"""生成 Mock 数据：合规规则、订单、商品、知识库片段。
运行：python scripts/gen_data.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


def dump(name, obj):
    path = DATA / name
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path} ({len(obj)} items)")


# ========================= 合规规则 24 条 =========================
RULES = [
    # ---------------- CN ----------------
    {
        "id": "CN-ADL-09", "market": "CN", "category": "*", "level": "L1", "action": "block",
        "clause": "广告法 第九条",
        "trigger": "绝对化用语",
        "patterns": ["最佳", "最好", "第一", "国家级", "顶级", "唯一", "史上最", "绝对", "100%"],
        "patterns_en": ["the best", "no.1", "no. 1", "number one", "100%", "perfect", "the only"],
        "exempt": [],
    },
    {
        "id": "CN-ADL-17", "market": "CN", "category": "*", "level": "L1", "action": "block",
        "clause": "广告法 第十七条",
        "trigger": "非医疗品宣称疾病治疗功能",
        "patterns": ["治疗", "治愈", "根治", "消炎", "抗癌", "降血压", "降血糖"],
        "patterns_en": ["cure", "treat", "heal", "anti-virus", "anticancer"],
        "exempt": ["不用于治疗", "不能治疗", "非药品", "不具治疗", "not intended to", "cannot treat", "does not treat"],
    },
    {
        "id": "CN-COS-22", "market": "CN", "category": "cosmetic", "level": "L2", "action": "rewrite",
        "clause": "化妆品监督管理条例 第二十二条",
        "trigger": "功效宣称缺乏依据",
        "patterns": ["美白淡斑", "抗敏修复", "祛斑", "生发", "即刻见效"],
        "patterns_en": ["whitening", "anti-allergy repair", "instant effect"],
        "exempt": [],
    },
    {
        "id": "CN-COS-23", "market": "CN", "category": "cosmetic", "level": "L1", "action": "block",
        "clause": "化妆品监督管理条例 第四十三条",
        "trigger": "化妆品宣称医疗作用",
        "patterns": ["药妆", "医用级", "消炎祛痘", "治疗痘痘", "修复创面"],
        "patterns_en": ["medical grade", "medicated", "treat acne"],
        "exempt": [],
    },
    {
        "id": "CN-FOOD-73", "market": "CN", "category": "supplement", "level": "L1", "action": "block",
        "clause": "食品安全法 第七十三条",
        "trigger": "食品宣称疾病预防治疗功能",
        "patterns": ["增强免疫力", "防癌", "调理亚健康", "排毒养生"],
        "patterns_en": ["boost immune system", "prevent cancer", "detox"],
        "exempt": [],
    },
    {
        "id": "CN-ADL-28", "market": "CN", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "广告法 第二十八条",
        "trigger": "虚假或未核实的时效承诺",
        "patterns": ["当天发货", "次日必达", "保证三天到", "绝不延误", "效果保障", "无效退款", "保证有效"],
        "patterns_en": ["same-day shipping guaranteed", "next-day guaranteed", "always arrives in 3 days"],
        "exempt": [],
    },
    {
        "id": "CN-ADL-11", "market": "CN", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "广告法 第十一条",
        "trigger": "贬低其他生产经营者的商品",
        "patterns": ["比别家好", "吊打同行", "其他品牌都是垃圾"],
        "patterns_en": ["better than other brands", "beats competitors"],
        "exempt": [],
    },
    {
        "id": "CN-POLICY-01", "market": "CN", "category": "*", "level": "L1", "action": "block",
        "clause": "商家售后政策 第 3 条",
        "trigger": "超出售后政策的退换承诺",
        "patterns": ["随时可退", "无条件退货", "假一赔十", "终身保修", "无限期"],
        "patterns_en": ["return anytime", "no questions asked return", "lifetime warranty"],
        "exempt": [],
    },
    # ---------------- EU ----------------
    {
        "id": "EU-COS-20", "market": "EU", "category": "cosmetic", "level": "L2", "action": "rewrite",
        "clause": "Reg.(EC) 1223/2009 Art.20；Reg.(EU) 655/2013",
        "trigger": "不可证实的功效宣称",
        "patterns": ["美白", "抗皱即刻消除", "永久祛斑", "逆转衰老"],
        "patterns_en": ["whitening", "wrinkle-free forever", "reverse aging", "permanent removal",
                        "fine lines", "disappear"],
        "exempt": [],
    },
    {
        "id": "EU-COS-655", "market": "EU", "category": "cosmetic", "level": "L2", "action": "rewrite",
        "clause": "Reg.(EU) 655/2013 第 3 条",
        "trigger": "误导性对比与无法验证的比较",
        "patterns": ["比大牌更好", "临床证明有效", "医生推荐率第一"],
        "patterns_en": ["better than premium brands", "clinically proven", "doctor recommended no.1"],
        "exempt": [],
    },
    {
        "id": "EU-MDR-745", "market": "EU", "category": "medical_device", "level": "L1", "action": "block",
        "clause": "Reg.(EU) 2017/745 (MDR)",
        "trigger": "未取得 CE 认证宣称医疗用途",
        "patterns": ["诊断", "预防疾病", "治疗疾病", "医疗级"],
        "patterns_en": ["diagnose", "prevent disease", "treat disease", "medical grade"],
        "exempt": ["已取得 CE", "CE certified", "not a medical device"],
    },
    {
        "id": "EU-GPSR-01", "market": "EU", "category": "*", "level": "L1", "action": "block",
        "clause": "Unfair Commercial Practices Directive 2005/29/EC",
        "trigger": "绝对化与无法证明的最高级表述",
        "patterns": ["最好", "第一", "100% 安全"],
        "patterns_en": ["the best", "no.1", "number one", "100% safe", "completely safe"],
        "exempt": [],
    },
    {
        "id": "EU-UCPD-02", "market": "EU", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "UCPD 2005/29/EC 附件一",
        "trigger": "虚假紧迫感与限量暗示",
        "patterns": ["最后 3 件", "马上涨价", "仅此一天"],
        "patterns_en": ["only 3 left", "price will rise", "today only", "only today",
                        "price doubles", "price will double", "last chance"],
        "exempt": [],
    },
    {
        "id": "EU-COS-ANX", "market": "EU", "category": "cosmetic", "level": "L1", "action": "block",
        "clause": "Reg.(EC) 1223/2009 Art.20 与附件",
        "trigger": "宣称绝对安全或零风险",
        "patterns": ["绝对安全", "无任何副作用", "零刺激"],
        "patterns_en": ["absolutely safe", "no side effects at all", "zero irritation"],
        "exempt": [],
    },
    {
        "id": "EU-DELIV-01", "market": "EU", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "消费者权益指令 2011/83/EU",
        "trigger": "无法保证的送达承诺",
        "patterns": ["保证送达", "必达"],
        "patterns_en": ["guaranteed delivery", "guaranteed 2-day delivery", "will definitely arrive",
                        "is guaranteed", "are guaranteed"],
        "exempt": [],
    },
    {
        "id": "EU-RETURN-01", "market": "EU", "category": "*", "level": "L1", "action": "block",
        "clause": "商家售后政策",
        "trigger": "超出商家售后政策期限的退货承诺",
        "patterns": ["终身退货", "无限期退货"],
        "patterns_en": ["lifetime return", "return anytime forever", "unlimited return period"],
        "exempt": [],
    },
    # ---------------- US ----------------
    {
        "id": "US-FDA-DSHEA", "market": "US", "category": "supplement", "level": "L1", "action": "block",
        "clause": "FD&C Act；DSHEA 1994",
        "trigger": "膳食补充剂疾病宣称",
        "patterns": ["治愈", "治疗"],
        "patterns_en": ["cure", "treat", "prevent", "diagnose", "heal"],
        # 动词 + 疾病实体的泛化写法，覆盖 reverse diabetes / relieve anxiety 这类未枚举表述
        "patterns_regex": [
            r"\b(?:cure|treat|prevent|diagnose|heal|reverse|relieve|eliminate)\w*\s+[\w\s]{0,40}?"
            r"(?:disease|diabetes|cancer|insomnia|anxiety|infection|illness|condition|symptoms?)\b"
        ],
        "exempt": [
            "not intended to diagnose", "not intended to treat", "not intended to cure",
            "not intended to prevent", "cannot treat", "does not treat", "does not cure",
            "not a treatment", "not a cure",
        ],
    },
    {
        "id": "US-FDA-101", "market": "US", "category": "supplement", "level": "L2", "action": "rewrite",
        "clause": "21 CFR 101.93",
        "trigger": "结构功能声明未加免责声明",
        "patterns": ["助眠", "改善睡眠", "缓解焦虑"],
        "patterns_en": ["supports sleep", "support restful sleep", "promotes relaxation",
                        "relieves anxiety", "boosts immunity", "helps you feel more relaxed"],
        "exempt": ["not intended to diagnose, treat, cure, or prevent any disease",
                   "not intended to diagnose, treat, cure, or prevent"],
        # requires = 前置条件：全文只要出现其中任一句，本条即视为已满足，不判违规
        "requires": ["not intended to diagnose", "not evaluated by the fda"],
    },
    {
        "id": "US-FTC-5", "market": "US", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "FTC Act §5",
        "trigger": "虚假或误导性广告",
        "patterns": ["保证有效", "绝对有效"],
        "patterns_en": ["guaranteed to work", "always works", "risk-free guaranteed",
                        "beats every competitor", "beats all competitors", "better than every",
                        "faster than any", "better than any", "cheaper than any"],
        "patterns_regex": [
            r"\b(?:faster|better|cheaper|stronger|safer)\s+than\s+(?:any|every|all)\b"
        ],
        "exempt": [],
    },
    {
        "id": "US-FTC-TEST", "market": "US", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "FTC Act §5；16 CFR 255",
        "trigger": "无证据的测试或认证宣称",
        "patterns": ["权威认证", "检测合格率 100%"],
        "patterns_en": ["certified by authorities", "lab tested 100%", "clinically tested and proven"],
        "exempt": [],
    },
    {
        "id": "US-FDA-COS", "market": "US", "category": "cosmetic", "level": "L1", "action": "block",
        "clause": "FD&C Act §201(g)；21 CFR 201.10",
        "trigger": "化妆品作出药品宣称",
        "patterns": ["治疗", "药效"],
        "patterns_en": ["treats skin disease", "heals wounds", "cures eczema", "treat acne", "prevents infection"],
        # 正则覆盖“动词 + 疾病实体”的变体，避免枚举式 patterns 漏掉 treats eczema / heals open wounds
        "patterns_regex": [
            r"\b(?:treat|heal|cure|prevent|diagnose)\w*\s+(?:the\s+|a\s+|any\s+|your\s+|open\s+)?"
            r"(?:skin\s+)?(?:disease|eczema|acne|insomnia|anxiety|infection|wounds?|burns?|diabetes|condition)s?\b"
        ],
        "exempt": ["not intended", "cosmetic only", "not a drug", "not for medical use"],
    },
    {
        "id": "US-REFUND-01", "market": "US", "category": "*", "level": "L1", "action": "block",
        "clause": "商家售后政策 第 3 条",
        "trigger": "超出售后政策的退款承诺",
        "patterns": ["全额退款无需退货", "马上退款"],
        "patterns_en": ["refund you 100% right away", "full refund immediately", "no questions asked refund",
                        "promise a full refund", "refund before", "refund without inspection"],
        "exempt": [],
    },
    {
        "id": "US-SHIP-01", "market": "US", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "FTC Act §5；商家物流政策",
        "trigger": "保证送达时效",
        "patterns": ["保证到货"],
        "patterns_en": ["guaranteed 2-day delivery", "will arrive in 3 days guaranteed",
                        "guaranteed to arrive", "guarantee delivery", "guaranteed delivery",
                        "delivery in 2 days", "delivery in 3 days"],
        "exempt": [],
    },
    {
        "id": "US-ENDORSE-01", "market": "US", "category": "*", "level": "L1", "action": "block",
        "clause": "16 CFR 255 Endorsement Guides",
        "trigger": "虚假用户评价或名人背书",
        "patterns": ["明星同款推荐", "100% 好评"],
        "patterns_en": ["celebrity endorsed", "100% positive reviews", "every customer loves it"],
        "exempt": [],
    },

    # ================= 菲律宾 PH =================
    {
        "id": "PH-FDA-01", "market": "PH", "category": "*", "level": "L1", "action": "block",
        "clause": "RA 9711 FDA Act；化妆品/食品不得宣称治疗（条款待核实）",
        "trigger": "宣称治疗或预防疾病",
        "patterns": ["治疗", "治愈", "根治"],
        "patterns_en": ["cure", "treat", "heal", "prevent disease", "kill bacteria"],
        "exempt": ["not intended", "cannot treat", "no claim"],
    },
    {
        "id": "PH-ADL-01", "market": "PH", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "RA 7394 Consumer Act Art. 110（条款待核实）",
        "trigger": "绝对化或无法证实的最高级表述",
        "patterns": ["最佳", "第一"],
        "patterns_en": ["the best", "no.1", "number one", "100% safe", "guaranteed"],
        "exempt": [],
    },
    {
        "id": "PH-SHIP-01", "market": "PH", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "RA 7394 Consumer Act Art. 117（条款待核实）",
        "trigger": "对到货时效做保证性承诺",
        "patterns": ["保证到货", "一定到"],
        "patterns_en": ["guaranteed delivery", "will arrive by", "definitely arrive", "no delays"],
        "exempt": [],
    },
    {
        "id": "PH-RETURN-01", "market": "PH", "category": "*", "level": "L1", "action": "block",
        "clause": "RA 7394 Consumer Act Art. 141；商家售后政策（条款待核实）",
        "trigger": "承诺超出政策的赔付或退换",
        "patterns": ["无条件退款", "任何情况都可退"],
        "patterns_en": ["full refund no questions", "refund anytime", "no inspection needed"],
        "exempt": [],
    },
    {
        "id": "PH-SUPPL-01", "market": "PH", "category": "supplement", "level": "L1", "action": "block",
        "clause": "Philippine FDA 膳食补充剂标示规定（条款待核实）",
        "trigger": "补充剂宣称疾病相关功效",
        "patterns": ["降血糖", "抗癌"],
        "patterns_en": ["lowers blood sugar", "fights cancer", "boosts immunity against"],
        "exempt": ["not intended", "cannot"],
    },

    # ================= 韩国 KR =================
    {
        "id": "KR-ADL-01", "market": "KR", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "표시광고법 第 3 条（条款待核实）",
        "trigger": "绝对化或最高级表述",
        "patterns": ["최고", "최상", "완벽", "1위", "唯一"],
        "patterns_en": ["the best", "perfect", "no.1"],
        "exempt": [],
    },
    {
        "id": "KR-COS-01", "market": "KR", "category": "cosmetic", "level": "L1", "action": "block",
        "clause": "화장품법 第 14 条 功能性化妆品标示（条款待核实）",
        "trigger": "未经审批宣称功能性功效",
        "patterns": ["주름 개선", "미백", "탈모 방지"],
        "patterns_en": ["wrinkle improvement", "whitening", "hair loss prevention"],
        "exempt": ["미승인", "not approved"],
    },
    {
        "id": "KR-DRUG-01", "market": "KR", "category": "*", "level": "L1", "action": "block",
        "clause": "약사법 药品与非药品区分（条款待核实）",
        "trigger": "非药品宣称治疗疾病",
        "patterns": ["치료", "치유", "완치"],
        "patterns_en": ["cure", "treat disease"],
        "exempt": ["치료 목적이 아닌", "not for treatment"],
    },
    {
        "id": "KR-SHIP-01", "market": "KR", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "전자상거래법 第 21 条（条款待核实）",
        "trigger": "对配送时效做保证性承诺",
        "patterns": ["반드시 도착", "무조건 배송"],
        "patterns_en": ["guaranteed delivery", "definitely arrive"],
        "exempt": [],
    },
    {
        "id": "KR-REFUND-01", "market": "KR", "category": "*", "level": "L1", "action": "block",
        "clause": "전자상거래법 第 17 条 清约撤回（条款待核实）",
        "trigger": "限制或排除法定退货权",
        "patterns": ["환불 불가", "교환 불가"],
        "patterns_en": ["no refunds", "no returns", "final sale no exchange"],
        "exempt": [],
    },

    # ================= 俄罗斯 RU =================
    {
        "id": "RU-ADL-01", "market": "RU", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "广告法 Federal Law No. 38-FZ Art. 5（条款待核实）",
        "trigger": "不实或绝对化的比较级表述",
        "patterns": ["лучший", "самый", "№1", "номер один"],
        "patterns_en": ["the best", "no.1"],
        "exempt": [],
    },
    {
        "id": "RU-MED-01", "market": "RU", "category": "*", "level": "L1", "action": "block",
        "clause": "广告法 Art. 24 药品与医疗广告（条款待核实）",
        "trigger": "非药品宣称治疗功效",
        "patterns": ["лечит", "излечивает", "вылечит"],
        "patterns_en": ["cures", "heals disease"],
        "exempt": ["не является лекарством", "not a medicine"],
    },
    {
        "id": "RU-SUPPL-01", "market": "RU", "category": "supplement", "level": "L1", "action": "block",
        "clause": "广告法 Art. 25 保健食品广告（条款待核实）",
        "trigger": "补充剂宣称疾病治疗效果",
        "patterns": ["понижает сахар", "против рака"],
        "patterns_en": ["lowers blood sugar", "fights cancer"],
        "exempt": ["не является лекарством"],
    },
    {
        "id": "RU-SHIP-01", "market": "RU", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "消费者权益保护法 No. 2300-1 Art. 10（条款待核实）",
        "trigger": "对交付时效做保证性承诺",
        "patterns": ["гарантированная доставка", "точно придет"],
        "patterns_en": ["guaranteed delivery", "will definitely arrive"],
        "exempt": [],
    },
    {
        "id": "RU-REFUND-01", "market": "RU", "category": "*", "level": "L1", "action": "block",
        "clause": "消费者权益保护法 No. 2300-1 Art. 26（条款待核实）",
        "trigger": "剥夺法定退货权",
        "patterns": ["возврат невозможен", "обмену не подлежит"],
        "patterns_en": ["no returns", "no exchange"],
        "exempt": [],
    },

    # ================= 蒙古 MN =================
    {
        "id": "MN-ADL-01", "market": "MN", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "广告法 Advertising Law Art. 6（条款待核实）",
        "trigger": "绝对化或误导性最高级表述",
        "patterns": ["хамгийн сайн", "хамгийн шилдэг"],
        "patterns_en": ["the best", "no.1"],
        "exempt": [],
    },
    {
        "id": "MN-MED-01", "market": "MN", "category": "*", "level": "L1", "action": "block",
        "clause": "广告法 Art. 8 医疗与药品广告（条款待核实）",
        "trigger": "非药品宣称治疗功效",
        "patterns": ["эмчилнэ", "эдгээнэ"],
        "patterns_en": ["cures", "treats disease"],
        "exempt": ["эм биш", "not a medicine"],
    },
    {
        "id": "MN-SUPPL-01", "market": "MN", "category": "supplement", "level": "L1", "action": "block",
        "clause": "卫生部 保健食品标示规定（条款待核实）",
        "trigger": "补充剂宣称疾病功效",
        "patterns": ["чихрийн шижин", "хорт хавдар"],
        "patterns_en": ["lowers blood sugar", "cancer"],
        "exempt": ["эм биш"],
    },
    {
        "id": "MN-SHIP-01", "market": "MN", "category": "*", "level": "L2", "action": "rewrite",
        "clause": "消费者保护法 Consumer Protection Law（条款待核实）",
        "trigger": "对时效做保证性承诺",
        "patterns": ["баталгаатай хүргэлт"],
        "patterns_en": ["guaranteed delivery"],
        "exempt": [],
    },
    {
        "id": "MN-REFUND-01", "market": "MN", "category": "*", "level": "L1", "action": "block",
        "clause": "消费者保护法 Consumer Protection Law（条款待核实）",
        "trigger": "限制法定退换权利",
        "patterns": ["буцаах боломжгүй"],
        "patterns_en": ["no refunds", "no returns"],
        "exempt": [],
    },
]

dump("rules.json", RULES)
print(f"规则 {len(RULES)} 条：" + " / ".join(f"{m} {sum(1 for r in RULES if r['market']==m)}" for m in ["CN","EU","US","PH","KR","RU","MN"]))
