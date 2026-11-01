# -*- coding: utf-8 -*-
"""统计 Agent 现有资料的覆盖情况，找出缺口。只读。"""
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

D = Path(r"D:\跨境智服\data")


def load(name):
    p = D / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


rules = load("rules.json") or []
kb = load("kb.json") or []
orders = load("orders.json") or []
products = load("products.json") or []
testset = load("testset.json") or []

print("=" * 60)
print("数量：rules=%d  kb=%d  orders=%d  products=%d  testset=%d"
      % (len(rules), len(kb), len(orders), len(products), len(testset)))
print("rules 字段:", sorted(rules[0].keys()) if rules else "-")
print("kb    字段:", sorted(kb[0].keys()) if kb else "-")
print("order 字段:", sorted(orders[0].keys()) if orders else "-")
print("prod  字段:", sorted(products[0].keys()) if products else "-")

print("\n" + "=" * 60)
print("【规则】市场 × 品类")
mat = defaultdict(Counter)
for r in rules:
    mat[r.get("market", "?")][r.get("category", "?")] += 1
cats = sorted({c for m in mat.values() for c in m})
print("%-6s %s  合计" % ("市场", "".join("%-16s" % c for c in cats)))
for m in sorted(mat):
    row = "".join("%-16s" % (mat[m].get(c, 0) or ".") for c in cats)
    print("%-6s %s  %d" % (m, row, sum(mat[m].values())))

lv = Counter(r.get("level", "?") for r in rules)
print("\n规则级别分布:", dict(lv))
print("带豁免条件的规则:", sum(1 for r in rules if r.get("exempt")))

print("\n" + "=" * 60)
print("【知识库】按 topic")
for k, v in Counter(i.get("topic", "?") for i in kb).most_common():
    print("  %-16s %d" % (k, v))
print("按市场:")
for k, v in Counter(i.get("market", "(通用)") for i in kb).most_common():
    print("  %-16s %d" % (k, v))

print("\n" + "=" * 60)
print("【订单】按市场")
for k, v in Counter(o.get("market", "?") for o in orders).most_common():
    print("  %-6s %d" % (k, v))
print("按状态:")
for k, v in Counter(o.get("status", "?") for o in orders).most_common():
    print("  %-20s %d" % (k, v))
print("有物流节点的:", sum(1 for o in orders if o.get("nodes")))

print("\n" + "=" * 60)
print("【商品】")
for p in products:
    print("  %-14s %-28s %-12s %s" % (p.get("sku", "-"), p.get("name", "-"),
                                      p.get("category", "-"), p.get("markets")))

print("\n" + "=" * 60)
print("【评测集】按 kind")
for k, v in Counter(t.get("kind", t.get("type", "?")) for t in testset).most_common():
    print("  %-16s %d" % (k, v))
