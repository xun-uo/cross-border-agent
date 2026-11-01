# -*- coding: utf-8 -*-
"""验证「后台改规则 → 判定立即生效」这条链路。改完自动恢复出厂规则。"""
import io
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\跨境智服")

from app import compliance, rules_store  # noqa: E402

TEXT = "이 제품은 항암 효과가 있습니다"   # 항암 只出现在 KR-SUP-8-1，不会被 8-2 抢
MARKET, CAT = "KR", "supplement"

rules = rules_store.load()
print("当前生效规则数:", len(rules))
print("修改前判定:", compliance.evaluate(TEXT, MARKET, CAT)["verdict"])

new_rules = []
for r in rules:
    r2 = dict(r)
    if r2["id"] == "KR-SUP-8-1":
        r2["patterns"] = ["__never_match__"]
        r2["patterns_en"] = ["__never_match__"]
        r2["action"] = "pass"
        r2["level"] = "L3"
    new_rules.append(r2)
rules_store.save(new_rules, note="verify-edit-takes-effect")
time.sleep(1.2)

ev = compliance.evaluate(TEXT, MARKET, CAT)
print("修改后判定:", ev["verdict"], "| 命中:", ev.get("clauses"))

ok = ev["verdict"] != "block"
rules_store.reset_default()
time.sleep(1.0)
after_reset = compliance.evaluate(TEXT, MARKET, CAT)["verdict"]
print("恢复出厂后判定:", after_reset)
print()
print("结论：", "✅ 后台编辑即时生效" if ok and after_reset == "block"
      else "❌ 仍不生效（ok=%s, reset=%s）" % (ok, after_reset))
