# -*- coding: utf-8 -*-
"""生成 Mock 订单 / 商品 / 知识库数据。运行：python scripts/gen_mock.py"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


def dump(name, obj):
    path = DATA / name
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {path} ({len(obj)} items)")


def order(no, market, lang, customer, items, status, status_cn, tracking, carrier,
          warehouse, shipped, eta_from, eta_to, nodes, cancellable=False,
          returnable=True, partial=False, refund="none"):
    return {
        "order_no": no, "market": market, "language": lang, "customer": customer,
        "items": items, "status": status, "status_cn": status_cn,
        "tracking_no": tracking, "carrier": carrier, "warehouse": warehouse,
        "shipped_at": shipped, "eta_from": eta_from, "eta_to": eta_to,
        "nodes": nodes, "cancellable": cancellable, "returnable": returnable,
        "partial": partial, "refund_status": refund,
    }


ORDERS = [
    # 1) 在途 · US · 演示主力单
    order("ORDER20261021001", "US", "en", "John Smith",
          [{"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "qty": 2, "category": "cosmetic"}],
          "in_transit", "在途", "CN20261021001", "YunExpress", "Guangxi",
          "2026-10-21", "2026-11-01", "2026-11-03",
          [{"time": "2026-10-21 09:12", "desc": "Order confirmed", "lat": 22.82, "lng": 108.32},
           {"time": "2026-10-21 18:40", "desc": "Picked up by carrier (Guangxi warehouse)", "lat": 22.82, "lng": 108.32},
           {"time": "2026-10-22 08:30", "desc": "Arrived at Shenzhen transit hub", "lat": 22.54, "lng": 114.06},
           {"time": "2026-10-23 07:20", "desc": "Departed origin facility", "lat": 22.54, "lng": 114.06},
           {"time": "2026-10-23 22:10", "desc": "Loaded on cross-border flight CAN → LAX", "lat": 23.13, "lng": 113.26},
           {"time": "2026-10-25 09:30", "desc": "Customs clearance in progress (Los Angeles)", "lat": 33.94, "lng": -118.41},
           {"time": "2026-10-25 11:05", "desc": "Arrived at US sorting center", "lat": 33.94, "lng": -118.41}],
          ),
    # 2) 已签收
    order("ORDER20261021002", "US", "en", "Emily Johnson",
          [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 1, "category": "supplement"}],
          "delivered", "已签收", "CN20261021002", "YunExpress", "Guangxi",
          "2026-10-05", "2026-10-18", "2026-10-20",
          [{"time": "2026-10-05 10:00", "desc": "Order confirmed"},
           {"time": "2026-10-18 09:30", "desc": "Out for delivery"},
           {"time": "2026-10-18 16:12", "desc": "Delivered, signed by E.J."}],
          ),
    # 3) 物流异常（滞留）
    order("ORDER20261021003", "EU", "de", "Anna Schmidt",
          [{"sku": "SKU-SKIN-02", "name": "Gentle Cleanser", "qty": 1, "category": "cosmetic"}],
          "exception", "物流异常（滞留）", "CN20261021003", "DHL eCommerce", "Guangxi",
          "2026-10-10", "2026-10-22", "2026-10-25",
          [{"time": "2026-10-10 12:00", "desc": "Order confirmed", "lat": 22.82, "lng": 108.32},
           {"time": "2026-10-10 20:30", "desc": "Picked up by carrier (Guangxi warehouse)", "lat": 22.82, "lng": 108.32},
           {"time": "2026-10-11 08:15", "desc": "Departed China (Shenzhen → Frankfurt)", "lat": 22.54, "lng": 114.06},
           {"time": "2026-10-13 16:20", "desc": "Arrived at Frankfurt customs", "lat": 50.11, "lng": 8.68},
           {"time": "2026-10-14 22:40", "desc": "Customs clearance in progress", "lat": 50.11, "lng": 8.68},
           {"time": "2026-10-18 03:10", "desc": "Shipment delayed at customs", "lat": 50.11, "lng": 8.68}],
          ),
    # 4) 待发货 · 可取消
    order("ORDER20261021004", "US", "en", "Michael Brown",
          [{"sku": "SKU-SKIN-03", "name": "Vitamin C Serum", "qty": 1, "category": "cosmetic"}],
          "pending", "待发货", "", "", "Guangxi",
          "", "", "",
          [{"time": "2026-10-21 21:30", "desc": "Order placed, awaiting fulfillment"}],
          cancellable=True,
          ),
    # 5) 多件部分发货
    order("ORDER20261021005", "US", "en", "Sarah Davis",
          [{"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "qty": 1, "category": "cosmetic"},
           {"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 2, "category": "supplement"}],
          "in_transit", "部分发货", "CN20261021005A", "YunExpress", "Guangxi",
          "2026-10-20", "2026-10-30", "2026-11-02",
          [{"time": "2026-10-20 08:00", "desc": "Order confirmed"},
           {"time": "2026-10-20 19:20", "desc": "1 of 2 items shipped (Hydra Repair Cream)"},
           {"time": "2026-10-21 10:00", "desc": "Remaining item pending stock"}],
          partial=True,
          ),
    # 6) 已取消
    order("ORDER20261021006", "EU", "fr", "Luc Martin",
          [{"sku": "SKU-SKIN-02", "name": "Gentle Cleanser", "qty": 1, "category": "cosmetic"}],
          "cancelled", "已取消", "", "", "Guangxi",
          "", "", "",
          [{"time": "2026-10-16 14:00", "desc": "Order cancelled by request"}],
          ),
    # 7) 退换处理中
    order("ORDER20261021007", "US", "en", "Jessica Wilson",
          [{"sku": "SKU-SKIN-03", "name": "Vitamin C Serum", "qty": 1, "category": "cosmetic"}],
          "return_in_progress", "退换处理中", "CN20261021007", "YunExpress", "Guangxi",
          "2026-09-28", "2026-10-10", "2026-10-12",
          [{"time": "2026-10-12 15:00", "desc": "Delivered"},
           {"time": "2026-10-15 09:00", "desc": "Return request received"},
           {"time": "2026-10-17 11:30", "desc": "Awaiting buyer photos"}],
          refund="pending",
          ),
    # 8) 在途 · EU
    order("ORDER20261021008", "EU", "es", "Carlos Ruiz",
          [{"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "qty": 1, "category": "cosmetic"}],
          "in_transit", "在途", "CN20261021008", "Correos", "Guangxi",
          "2026-10-19", "2026-10-29", "2026-11-01",
          [{"time": "2026-10-19 09:00", "desc": "Pedido confirmado"},
           {"time": "2026-10-20 07:30", "desc": "Salida del almacén"}],
          ),
    # 9) 在途 · 拉美（西语演示）
    order("ORDER20261021009", "LATAM", "es", "María González",
          [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 1, "category": "supplement"}],
          "in_transit", "在途", "CN20261021009", "YunExpress", "Guangxi",
          "2026-10-18", "2026-11-05", "2026-11-10",
          [{"time": "2026-10-18 10:00", "desc": "Pedido confirmado"},
           {"time": "2026-10-19 08:00", "desc": "En tránsito"}],
          ),
    # 10) 已签收 · EU
    order("ORDER20261021010", "EU", "de", "Thomas Müller",
          [{"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "qty": 3, "category": "cosmetic"}],
          "delivered", "已签收", "CN20261021010", "DHL eCommerce", "Guangxi",
          "2026-10-02", "2026-10-15", "2026-10-17",
          [{"time": "2026-10-02 11:00", "desc": "Bestellung bestätigt"},
           {"time": "2026-10-15 14:00", "desc": "Zugestellt"}],
          ),
    # 11) 异常 · 丢失
    order("ORDER20261021011", "US", "en", "David Lee",
          [{"sku": "SKU-SKIN-03", "name": "Vitamin C Serum", "qty": 1, "category": "cosmetic"}],
          "lost", "物流丢失", "CN20261021011", "YunExpress", "Guangxi",
          "2026-10-08", "2026-10-20", "2026-10-23",
          [{"time": "2026-10-08 09:00", "desc": "Order confirmed"},
           {"time": "2026-10-12 10:00", "desc": "In transit"},
           {"time": "2026-10-20 17:00", "desc": "Shipment reported lost by carrier"}],
          ),
    # 12) 待发货 · 不可取消
    order("ORDER20261021012", "US", "en", "Linda Martinez",
          [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 1, "category": "supplement"}],
          "processing", "打包中", "", "", "Guangxi",
          "", "2026-10-28", "2026-10-30",
          [{"time": "2026-10-21 16:00", "desc": "Order confirmed, packing"}],
          cancellable=False,
          ),
    # 13) 已退款
    order("ORDER20261021013", "EU", "fr", "Sophie Bernard",
          [{"sku": "SKU-SKIN-02", "name": "Gentle Cleanser", "qty": 1, "category": "cosmetic"}],
          "refunded", "已退款", "CN20261021013", "Colissimo", "Guangxi",
          "2026-09-20", "2026-10-02", "2026-10-04",
          [{"time": "2026-09-20 10:00", "desc": "Commande confirmée"},
           {"time": "2026-10-04 12:00", "desc": "Livrée"},
           {"time": "2026-10-10 09:00", "desc": "Remboursement effectué"}],
          refund="done",
          ),
    # 14) 在途 · 演示用第二主力单
    order("ORDER20261021014", "US", "en", "Robert Taylor",
          [{"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "qty": 1, "category": "cosmetic"}],
          "in_transit", "在途", "CN20261021014", "YunExpress", "Guangxi",
          "2026-10-22", "2026-11-02", "2026-11-05",
          [{"time": "2026-10-22 08:00", "desc": "Order confirmed"},
           {"time": "2026-10-22 20:00", "desc": "Departed Guangxi warehouse"}],
          ),
    # 15) 已签收 · US
    order("ORDER20261021015", "US", "en", "Karen White",
          [{"sku": "SKU-SKIN-02", "name": "Gentle Cleanser", "qty": 2, "category": "cosmetic"}],
          "delivered", "已签收", "CN20261021015", "YunExpress", "Guangxi",
          "2026-10-01", "2026-10-14", "2026-10-16",
          [{"time": "2026-10-16 13:00", "desc": "Delivered"}],
          ),
    # 16) 部分发货 · 三件套
    order("ORDER20261021016", "EU", "de", "Julia Wagner",
          [{"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "qty": 1, "category": "cosmetic"},
           {"sku": "SKU-SKIN-02", "name": "Gentle Cleanser", "qty": 1, "category": "cosmetic"},
           {"sku": "SKU-SKIN-03", "name": "Vitamin C Serum", "qty": 1, "category": "cosmetic"}],
          "in_transit", "部分发货", "CN20261021016A", "DHL eCommerce", "Guangxi",
          "2026-10-21", "2026-11-01", "2026-11-04",
          [{"time": "2026-10-21 09:00", "desc": "Order confirmed"},
           {"time": "2026-10-21 22:00", "desc": "2 of 3 items shipped"},
           {"time": "2026-10-22 08:00", "desc": "1 item awaiting restock"}],
          partial=True,
          ),
    # 17) 清关异常
    order("ORDER20261021017", "EU", "es", "Ana López",
          [{"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "qty": 2, "category": "supplement"}],
          "customs_hold", "清关扣留", "CN20261021017", "Correos", "Guangxi",
          "2026-10-09", "2026-10-24", "2026-10-27",
          [{"time": "2026-10-09 10:00", "desc": "Pedido confirmado"},
           {"time": "2026-10-15 08:00", "desc": "Retenido en aduana"},
           {"time": "2026-10-18 09:00", "desc": "Documentos requeridos por aduana"}],
          ),
    # 18) 在途 · US
    order("ORDER20261021018", "US", "en", "James Anderson",
          [{"sku": "SKU-SKIN-03", "name": "Vitamin C Serum", "qty": 1, "category": "cosmetic"}],
          "in_transit", "在途", "CN20261021018", "YunExpress", "Guangxi",
          "2026-10-20", "2026-11-01", "2026-11-04",
          [{"time": "2026-10-20 09:00", "desc": "Order confirmed"},
           {"time": "2026-10-21 10:00", "desc": "In transit"}],
          ),
    # 19) 已签收 · LATAM
    order("ORDER20261021019", "LATAM", "es", "Luis Fernández",
          [{"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "qty": 1, "category": "cosmetic"}],
          "delivered", "已签收", "CN20261021019", "YunExpress", "Guangxi",
          "2026-09-30", "2026-10-16", "2026-10-18",
          [{"time": "2026-10-18 11:00", "desc": "Entregado"}],
          ),
    # 20) 待发货 · 可取消
    order("ORDER20261021020", "EU", "fr", "Nathalie Roux",
          [{"sku": "SKU-SKIN-02", "name": "Gentle Cleanser", "qty": 1, "category": "cosmetic"}],
          "pending", "待发货", "", "", "Guangxi",
          "", "", "",
          [{"time": "2026-10-22 06:30", "desc": "Commande reçue"}],
          cancellable=True,
          ),
]

dump("orders.json", ORDERS)

# ========================= 商品 =========================
PRODUCTS = [
    {"sku": "SKU-SKIN-01", "name": "Hydra Repair Cream", "category": "cosmetic", "market": ["US", "EU"],
     "desc": "Moisturizing face cream with ceramides and hyaluronic acid.",
     "claims_allowed": ["moisturizes", "supports the skin barrier", "suitable for dry skin"],
     "claims_forbidden": ["cure eczema", "treat skin disease", "heal wounds"],
     "note": "彩妆/护肤类，不得作疾病宣称。"},
    {"sku": "SKU-SKIN-02", "name": "Gentle Cleanser", "category": "cosmetic", "market": ["US", "EU"],
     "desc": "Fragrance-free daily cleanser for sensitive skin.",
     "claims_allowed": ["gentle cleansing", "fragrance-free", "for sensitive skin"],
     "claims_forbidden": ["anti-allergy", "medical grade", "treat acne"],
     "note": "敏感肌可用，但不得称抗敏/医用级。"},
    {"sku": "SKU-SKIN-03", "name": "Vitamin C Serum", "category": "cosmetic", "market": ["US", "EU"],
     "desc": "Brightening serum with 10% vitamin C.",
     "claims_allowed": ["brightens the look of skin", "antioxidant support"],
     "claims_forbidden": ["whitening", "permanent removal of spots", "reverse aging"],
     "note": "美国可做结构功能声明；欧盟须有功效证据。"},
    {"sku": "SKU-SUP-01", "name": "Calm Sleep Supplement", "category": "supplement", "market": ["US", "EU", "LATAM"],
     "desc": "Melatonin-free sleep support supplement with L-theanine.",
     "claims_allowed": ["supports relaxation", "helps you unwind"],
     "claims_forbidden": ["cure insomnia", "treat anxiety", "cure any disease"],
     "note": "美国须附 DSHEA 免责声明：not intended to diagnose, treat, cure, or prevent any disease."},
]

dump("products.json", PRODUCTS)

# ========================= 知识库片段 =========================
KB = [
    {"id": "KB-01", "market": "*", "topic": "return_policy", "title": "退货政策（总则）",
     "text": "签收后 14 天内可申请退货，需商品未使用、包装完整。破损或错发需提供外包装与商品照片，确认后可补发或退款。"},
    {"id": "KB-02", "market": "EU", "topic": "return_policy", "title": "EU 14 天冷静期",
     "text": "欧盟消费者享有无理由退货权，期限为收到商品起 14 天。商家不得以政策条款缩短该期限。"},
    {"id": "KB-03", "market": "US", "topic": "return_policy", "title": "US 退货政策",
     "text": "美国站执行商家统一政策：签收后 30 天内可申请退货。运费承担按责任方判定。"},
    {"id": "KB-04", "market": "*", "topic": "shipping", "title": "物流时效",
     "text": "默认发 YunExpress / DHL eCommerce，平均 7-15 个工作日送达。清关高峰期可能延长。运费按重量与目的地结算。"},
    {"id": "KB-05", "market": "*", "topic": "compliance", "title": "绝对化用语禁用清单",
     "text": "禁止使用 best / No.1 / 100% safe / perfect 等绝对化表述，无论是否附加说明。"},
    {"id": "KB-06", "market": "US", "topic": "compliance", "title": "膳食补充剂免责声明",
     "text": "任何结构功能声明必须同时附上：This statement has not been evaluated by the FDA. This product is not intended to diagnose, treat, cure, or prevent any disease."},
    {"id": "KB-07", "market": "EU", "topic": "compliance", "title": "化妆品功效宣称",
     "text": "宣称须满足透明、真实、有证据支持、诚实、公平、消费者知情六项通用标准，且需备有功效证据文件。"},
    {"id": "KB-08", "market": "*", "topic": "damage", "title": "破损处理",
     "text": "买家提供照片后，48 小时内确认。确认属实可免费补发或全额退款。不得在确认前承诺退款。"},
    {"id": "KB-09", "market": "*", "topic": "handover", "title": "转人工规则",
     "text": "涉及平台处罚、大额赔付、法律争议、买家明确要求人工的，一律转人工，不自行承诺。"},
    {"id": "KB-10", "market": "*", "topic": "customs", "title": "清关异常处理",
     "text": "清关扣留需买家提供身份证明或补充申报材料，商家协助提交。不得承诺一定能放行。"},
]

dump("kb.json", KB)
