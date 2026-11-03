# -*- coding: utf-8 -*-
"""追加 #50：买家自报的假订单号覆盖了登录绑定的真订单。"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROW = (
    "| 50 | 买家端 · 假订单号覆盖绑定订单，导致反复索要订单号/运单号 | "
    "买家连着发「查一下这个包裹的物流信息 ORDER20261028888」（这是**库里没有**的订单号），"
    "AI 回的是「请提供一下运单号」「请提供一下订单号」「请提供一下您想咨询的具体问题」，"
    "还有一条只说「我需要先为您查询，请稍等」——**买家明明已凭订单号登录**，"
    "系统却当他是没身份的路人，反复要单号 | "
    "⬜ 待修（2026-11-03 23:16–23:21 报，五张截图）。<br>"
    "**根因（代码可定位）**：`process()` 里写的是 `order = find_order(intent.get(\"order_no\") or bound_order)` —— "
    "买家话里那个**假订单号**会被 `extract_order_no()` 抽出来放进 `intent[\"order_no\"]`，"
    "于是 `or` 直接把 `bound_order` 短路掉；而 `find_order(假号)` 返回 `None` → "
    "整轮没有任何订单资料 → 模型只能自由发挥，开始要运单号（#50），"
    "同时 `need_order and not order and not intent.get(\"order_no\")` 这个追问分支又因为假号非空而不触发。"
    "本质和 #46③ 同源，但那条只加了提示词，挡不住这种「数据为空」的情况。<br>"
    "**修法**：① `order = find_order(intent.get(\"order_no\") or \"\") or find_order(bound_order)` —— "
    "先按买家说的查，查不到就退回登录绑定的那一单；② 假号且**没有**绑定订单时，"
    "把 `intent[\"order_no\"]` 清空并记 `_order_no_not_found`，让既有的「缺订单号 → 追问」分支接管"
    "（用固定话术问，而不是让模型自由发挥）；③ 命中①时在 `intent` 上记 `_order_no_ignored`，方便调试面板看出「忽略了他写的号」。<br>"
    "**回归要点**：真订单号照常查得到；假订单号 + 已绑定 → 用绑定那单回答；假订单号 + 未绑定 → 明确请他确认订单号。|"
)

PATH = r"D:\跨境智服\待修清单.md"
s = io.open(PATH, encoding="utf-8").read().rstrip("\n")
io.open(PATH, "w", encoding="utf-8", newline="\n").write(s + "\n" + ROW + "\n")

rows = [ln for ln in io.open(PATH, encoding="utf-8").read().split("\n")
        if re.match(r"^\|\s*\d+\s*\|", ln)]
ids = [re.match(r"^\|\s*(\d+)", ln).group(1) for ln in rows]
print("总行数:", len(rows), "| 最后编号:", ids[-1], "| 重复:", [x for x in set(ids) if ids.count(x) > 1])
