# -*- coding: utf-8 -*-
"""补英国、日本订单各 2 单 + 知识库 4 条（退货/清关）。"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

D = Path(r"D:\跨境智服\data")

SHA = (31.23, 121.47)
SZ = (22.54, 114.06)
LHR = (51.51, -0.13)
MAN = (53.48, -2.24)
TYO = (35.68, 139.69)
OSA = (34.69, 135.50)


def nd(t, d, c):
    return {"time": t, "desc": d, "lat": c[0], "lng": c[1]}


NEW = [
    {
        "order_no": "ORDER20261021031", "market": "UK", "language": "en",
        "customer": "Emma Wilson",
        "items": [{"sku": "SKU-SKIN-03", "name": "Vitamin C Serum", "qty": 1,
                   "category": "cosmetic"}],
        "status": "in_transit", "status_cn": "在途",
        "tracking_no": "UK20261021031", "carrier": "Royal Mail",
        "warehouse": "Shanghai", "shipped_at": "2026-10-28",
        "eta_from": "2026-11-05", "eta_to": "2026-11-09",
        "nodes": [
            nd("2026-10-28 09:30", "Order confirmed", SHA),
            nd("2026-10-28 18:15", "Picked up by carrier (Shanghai warehouse)", SHA),
            nd("2026-10-30 07:40", "Departed origin facility", SZ),
            nd("2026-11-02 11:20", "Arrived at London Heathrow clearance hub", LHR),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000031",
    },
    {
        "order_no": "ORDER20261021032", "market": "UK", "language": "en",
        "customer": "James Taylor",
        "items": [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 2,
                   "category": "supplement"}],
        "status": "customs_hold", "status_cn": "清关滞留",
        "tracking_no": "UK20261021032", "carrier": "Royal Mail",
        "warehouse": "Shanghai", "shipped_at": "2026-10-24",
        "eta_from": "2026-11-04", "eta_to": "2026-11-10",
        "nodes": [
            nd("2026-10-24 10:05", "Order confirmed", SHA),
            nd("2026-10-24 19:30", "Picked up by carrier", SHA),
            nd("2026-10-27 08:50", "Departed origin facility", SZ),
            nd("2026-10-31 14:10", "Arrived at London Heathrow clearance hub", LHR),
            nd("2026-11-01 09:25", "Held by HMRC — awaiting importer documentation", LHR),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000032",
    },
    {
        "order_no": "ORDER20261021033", "market": "JP", "language": "en",
        "customer": "佐藤 美咲",
        "items": [{"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "qty": 1,
                   "category": "cosmetic"}],
        "status": "in_transit", "status_cn": "在途",
        "tracking_no": "JP20261021033", "carrier": "Sagawa Express",
        "warehouse": "Shanghai", "shipped_at": "2026-10-29",
        "eta_from": "2026-11-02", "eta_to": "2026-11-05",
        "nodes": [
            nd("2026-10-29 09:15", "Order confirmed", SHA),
            nd("2026-10-29 17:45", "Picked up by carrier (Shanghai warehouse)", SHA),
            nd("2026-10-31 06:30", "Departed on cross-border flight PVG → NRT", SZ),
            nd("2026-11-01 08:20", "Arrived at Tokyo customs", TYO),
            nd("2026-11-01 16:40", "Customs cleared", TYO),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000033",
    },
    {
        "order_no": "ORDER20261021034", "market": "JP", "language": "en",
        "customer": "田中 健太",
        "items": [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 1,
                   "category": "supplement"}],
        "status": "customs_hold", "status_cn": "清关滞留",
        "tracking_no": "JP20261021034", "carrier": "Sagawa Express",
        "warehouse": "Shanghai", "shipped_at": "2026-10-23",
        "eta_from": "2026-11-03", "eta_to": "2026-11-08",
        "nodes": [
            nd("2026-10-23 09:40", "Order confirmed", SHA),
            nd("2026-10-23 18:20", "Picked up by carrier", SHA),
            nd("2026-10-26 07:10", "Departed origin facility", SZ),
            nd("2026-10-29 10:35", "Arrived at Osaka customs", OSA),
            nd("2026-10-30 15:50", "Held by customs — ingredient documentation required", OSA),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000034",
    },
]

op = D / "orders.json"
orders = json.loads(op.read_text(encoding="utf-8"))
have = {o["order_no"] for o in orders}
added = 0
for o in NEW:
    if o["order_no"] not in have:
        orders.append(o)
        added += 1
orders.sort(key=lambda x: x["order_no"])
op.write_text(json.dumps(orders, ensure_ascii=False, indent=1), encoding="utf-8")
print("订单：新增 %d，当前共 %d" % (added, len(orders)))

KB = [
    {"id": "KB-37", "market": "UK", "topic": "return_policy",
     "title": "英国 · 14 天冷静期",
     "text": "英国消费者合同（信息、取消与附加收费）条例 2013 规定，远程销售的消费者自收到商品起 14 天内"
             "可无理由取消订单，并在此后再有 14 天把商品退回。定制商品、易腐品、拆封的音像制品与软件等除外。"
             "　关键词：退货 return refund 退款 退换 exchange 冷静期 cooling-off 英国 UK"},
    {"id": "KB-38", "market": "JP", "topic": "return_policy",
     "title": "日本 · 通信販売的返品特約",
     "text": "日本的通信販売（网购）没有法定クーリング・オフ。但依特定商取引法第 15 条の2，"
             "卖家必须在页面上明示退货特约（能否退货、期限、运费由谁承担）；"
             "若未明示，消费者可在收到商品后 8 天内退货。"
             "　关键词：退货 return 返品 退款 返金 退换 交換 日本 Japan"},
    {"id": "KB-39", "market": "UK", "topic": "customs",
     "title": "英国 · 135 英镑进口起征点",
     "text": "英国对货值 135 英镑及以下的进口商品免征关税，且由卖家在销售时代收增值税（VAT），"
             "买家不再另付进口环节费用；超过 135 英镑则按正常进口程序申报缴税。"
             "具体以 HMRC 当期规定为准。"
             "　关键词：关税 customs duty 清关 VAT 免税额 英国 UK"},
    {"id": "KB-40", "market": "JP", "topic": "customs",
     "title": "日本 · 个人进口免税额",
     "text": "日本对个人自用进口物品，课税价格在 1 万日元以下免征关税与消费税；"
             "超过则按商品类别税率征收。酒类、香烟等不适用该免税额度。具体以日本海关当期规定为准。"
             "　关键词：关税 customs 関税 清关 通関 免税额 日本 Japan"},
]

kp = D / "kb.json"
kb = json.loads(kp.read_text(encoding="utf-8"))
have = {k["id"] for k in kb}
added = 0
for k in KB:
    if k["id"] not in have:
        kb.append(k)
        added += 1
kp.write_text(json.dumps(kb, ensure_ascii=False, indent=1), encoding="utf-8")
print("知识库：新增 %d，当前共 %d" % (added, len(kb)))
