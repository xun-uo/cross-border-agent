# -*- coding: utf-8 -*-
"""补齐 PH/KR/RU/MN/CN 五个市场的订单，并扩展商品的市场覆盖。幂等：已存在则跳过。"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

D = Path(r"D:\跨境智服\data")

# 坐标
GZ = (23.13, 113.26)
SZ = (22.54, 114.06)
MNL = (14.60, 120.98)
WH = (37.51, 122.12)
ICN = (37.46, 126.71)
MZL = (49.60, 117.43)
NSK = (55.03, 82.92)
MOW = (55.75, 37.62)
ELE = (43.65, 111.98)
ULN = (47.89, 106.91)
HGH = (30.27, 120.15)
PEK = (39.90, 116.41)
SHA = (31.23, 121.47)


def nd(t, d, c):
    return {"time": t, "desc": d, "lat": c[0], "lng": c[1]}


NEW = [
    {
        "order_no": "ORDER20261021021", "market": "PH", "language": "en",
        "customer": "Maria Santos",
        "items": [{"sku": "SKU-SKIN-02", "name": "Gentle Cleanser", "qty": 1,
                   "category": "cosmetic"}],
        "status": "in_transit", "status_cn": "在途",
        "tracking_no": "PH20261021021", "carrier": "Flash Express",
        "warehouse": "Guangzhou", "shipped_at": "2026-10-27",
        "eta_from": "2026-11-02", "eta_to": "2026-11-05",
        "nodes": [
            nd("2026-10-27 10:05", "Order confirmed", GZ),
            nd("2026-10-27 19:30", "Picked up by carrier (Guangzhou warehouse)", GZ),
            nd("2026-10-28 11:40", "Departed origin facility", SZ),
            nd("2026-10-30 08:15", "Arrived at Manila sorting center", MNL),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000021",
    },
    {
        "order_no": "ORDER20261021022", "market": "PH", "language": "en",
        "customer": "Jose Reyes",
        "items": [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 1,
                   "category": "supplement"}],
        "status": "customs_hold", "status_cn": "清关滞留",
        "tracking_no": "PH20261021022", "carrier": "YunExpress",
        "warehouse": "Guangzhou", "shipped_at": "2026-10-24",
        "eta_from": "2026-11-03", "eta_to": "2026-11-08",
        "nodes": [
            nd("2026-10-24 09:20", "Order confirmed", GZ),
            nd("2026-10-24 20:10", "Picked up by carrier", GZ),
            nd("2026-10-26 07:35", "Departed origin facility", SZ),
            nd("2026-10-28 14:50", "Arrived at Manila customs", MNL),
            nd("2026-10-29 09:05", "Held by customs — awaiting importer documents", MNL),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000022",
    },
    {
        "order_no": "ORDER20261021023", "market": "KR", "language": "en",
        "customer": "Kim Min-ji",
        "items": [{"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "qty": 1,
                   "category": "cosmetic"}],
        "status": "in_transit", "status_cn": "在途",
        "tracking_no": "KR20261021023", "carrier": "CJ Logistics",
        "warehouse": "Weihai", "shipped_at": "2026-10-28",
        "eta_from": "2026-11-01", "eta_to": "2026-11-03",
        "nodes": [
            nd("2026-10-28 08:40", "Order confirmed", WH),
            nd("2026-10-28 17:25", "Picked up by carrier (Weihai warehouse)", WH),
            nd("2026-10-29 09:10", "Departed on cross-border ferry WH → ICN", WH),
            nd("2026-10-30 07:00", "Arrived at Incheon port", ICN),
            nd("2026-10-30 15:20", "Customs cleared", ICN),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000023",
    },
    {
        "order_no": "ORDER20261021024", "market": "KR", "language": "en",
        "customer": "Park Ji-hoon",
        "items": [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 2,
                   "category": "supplement"}],
        "status": "delivered", "status_cn": "已送达",
        "tracking_no": "KR20261021024", "carrier": "CJ Logistics",
        "warehouse": "Weihai", "shipped_at": "2026-10-20",
        "eta_from": "2026-10-23", "eta_to": "2026-10-25",
        "nodes": [
            nd("2026-10-20 09:15", "Order confirmed", WH),
            nd("2026-10-20 18:50", "Picked up by carrier", WH),
            nd("2026-10-22 06:30", "Arrived at Incheon port", ICN),
            nd("2026-10-23 10:40", "Out for delivery (Seoul)", ICN),
            nd("2026-10-23 16:05", "Delivered, signed by recipient", ICN),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000024",
    },
    {
        "order_no": "ORDER20261021025", "market": "RU", "language": "en",
        "customer": "Anna Ivanova",
        "items": [{"sku": "SKU-SKIN-03", "name": "Vitamin C Serum", "qty": 1,
                   "category": "cosmetic"}],
        "status": "in_transit", "status_cn": "在途",
        "tracking_no": "RU20261021025", "carrier": "CDEK",
        "warehouse": "Manzhouli", "shipped_at": "2026-10-25",
        "eta_from": "2026-11-08", "eta_to": "2026-11-15",
        "nodes": [
            nd("2026-10-25 11:00", "Order confirmed", MZL),
            nd("2026-10-25 21:30", "Picked up by carrier (Manzhouli warehouse)", MZL),
            nd("2026-10-27 08:45", "Crossed border at Manzhouli checkpoint", MZL),
            nd("2026-10-30 13:20", "Arrived at Novosibirsk transit hub", NSK),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000025",
    },
    {
        "order_no": "ORDER20261021026", "market": "RU", "language": "en",
        "customer": "Dmitry Volkov",
        "items": [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 1,
                   "category": "supplement"}],
        "status": "return_in_progress", "status_cn": "退货处理中",
        "tracking_no": "RU20261021026", "carrier": "CDEK",
        "warehouse": "Manzhouli", "shipped_at": "2026-10-12",
        "eta_from": "2026-10-20", "eta_to": "2026-10-26",
        "nodes": [
            nd("2026-10-12 10:30", "Order confirmed", MZL),
            nd("2026-10-13 09:00", "Picked up by carrier", MZL),
            nd("2026-10-18 17:40", "Arrived in Moscow", MOW),
            nd("2026-10-20 14:15", "Delivered", MOW),
            nd("2026-10-23 10:05", "Return requested by customer", MOW),
            nd("2026-10-26 08:20", "Parcel in transit back to seller", NSK),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "pending", "phone": "13800000026",
    },
    {
        "order_no": "ORDER20261021027", "market": "MN", "language": "en",
        "customer": "Batbayar Erdene",
        "items": [{"sku": "SKU-SKIN-02", "name": "Gentle Cleanser", "qty": 2,
                   "category": "cosmetic"}],
        "status": "in_transit", "status_cn": "在途",
        "tracking_no": "MN20261021027", "carrier": "Mongol Post",
        "warehouse": "Erenhot", "shipped_at": "2026-10-26",
        "eta_from": "2026-11-04", "eta_to": "2026-11-09",
        "nodes": [
            nd("2026-10-26 09:50", "Order confirmed", ELE),
            nd("2026-10-26 20:15", "Picked up by carrier (Erenhot warehouse)", ELE),
            nd("2026-10-28 07:30", "Crossed border at Zamyn-Uud", ELE),
            nd("2026-10-31 12:45", "Arrived at Ulaanbaatar sorting center", ULN),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000027",
    },
    {
        "order_no": "ORDER20261021028", "market": "MN", "language": "en",
        "customer": "Saruul Altangerel",
        "items": [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 1,
                   "category": "supplement"}],
        "status": "exception", "status_cn": "派送异常",
        "tracking_no": "MN20261021028", "carrier": "Mongol Post",
        "warehouse": "Erenhot", "shipped_at": "2026-10-18",
        "eta_from": "2026-10-28", "eta_to": "2026-11-02",
        "nodes": [
            nd("2026-10-18 08:25", "Order confirmed", ELE),
            nd("2026-10-18 16:40", "Picked up by carrier", ELE),
            nd("2026-10-22 09:05", "Arrived at Ulaanbaatar sorting center", ULN),
            nd("2026-10-24 11:30", "Delivery attempted — no one at address", ULN),
            nd("2026-10-27 10:00", "Delivery failed again — address unreachable", ULN),
        ],
        "cancellable": True, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000028",
    },
    {
        "order_no": "ORDER20261021029", "market": "CN", "language": "zh",
        "customer": "王芳",
        "items": [{"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "qty": 1,
                   "category": "cosmetic"}],
        "status": "delivered", "status_cn": "已送达",
        "tracking_no": "SF20261021029", "carrier": "顺丰速运",
        "warehouse": "Hangzhou", "shipped_at": "2026-10-22",
        "eta_from": "2026-10-24", "eta_to": "2026-10-25",
        "nodes": [
            nd("2026-10-22 10:10", "订单已确认", HGH),
            nd("2026-10-22 15:30", "杭州仓已揽收", HGH),
            nd("2026-10-23 08:20", "到达上海转运中心", SHA),
            nd("2026-10-24 09:45", "派送中", PEK),
            nd("2026-10-24 14:20", "已签收，本人签收", PEK),
        ],
        "cancellable": False, "returnable": True, "partial": False,
        "refund_status": "none", "phone": "13800000029",
    },
    {
        "order_no": "ORDER20261021030", "market": "CN", "language": "zh",
        "customer": "李明",
        "items": [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 1,
                   "category": "supplement"}],
        "status": "refunded", "status_cn": "已退款",
        "tracking_no": "ZT20261021030", "carrier": "中通快递",
        "warehouse": "Hangzhou", "shipped_at": "2026-10-15",
        "eta_from": "2026-10-18", "eta_to": "2026-10-20",
        "nodes": [
            nd("2026-10-15 09:35", "订单已确认", HGH),
            nd("2026-10-15 18:00", "杭州仓已揽收", HGH),
            nd("2026-10-17 07:50", "到达北京转运中心", PEK),
            nd("2026-10-18 10:30", "派送中", PEK),
            nd("2026-10-18 16:10", "买家申请退款：商品破损", PEK),
            nd("2026-10-20 11:00", "退款已完成", PEK),
        ],
        "cancellable": False, "returnable": False, "partial": False,
        "refund_status": "done", "phone": "13800000030",
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

# ---- 商品：补市场覆盖 + 加一个医疗器械 ----
pp = D / "products.json"
products = json.loads(pp.read_text(encoding="utf-8"))
ALL = ["US", "EU", "CN", "KR", "MN", "PH", "RU"]
for p in products:
    cur = p.get("market") or []
    merged = list(dict.fromkeys(list(cur) + ALL))
    if p.get("sku") == "SKU-SUP-01" and "LATAM" not in merged:
        merged.append("LATAM")
    p["market"] = merged

if not any(p.get("sku") == "SKU-MED-01" for p in products):
    products.append({
        "sku": "SKU-MED-01",
        "name": "Digital Thermometer Pro",
        "category": "medical_device",
        "desc": "家用电子体温计，接触式测温，测量范围 32.0–42.9°C。",
        "market": ["US", "EU", "CN"],
        "claims_allowed": ["测量体温", "家用健康监测", "accurate body temperature reading"],
        "claims_forbidden": ["诊断疾病", "替代就医", "治疗发热", "diagnose", "treat fever", "replace a doctor"],
        "note": "医疗器械类：不得作疾病诊断或治疗宣称，须标注非专业医疗设备。",
    })
pp.write_text(json.dumps(products, ensure_ascii=False, indent=1), encoding="utf-8")
print("商品：当前共 %d 个 -> %s" % (len(products), [p["sku"] for p in products]))
