# -*- coding: utf-8 -*-
"""修掉上一步写重了的状态前缀（每个前缀连着出现两次）。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PATH = r"D:\跨境智服\待修清单.md"
PREFIXES = [
    "🔧 #120 已修（390 宽实测宽 132px、不再撑满整行） ",
    "🔧 #120 已修（390 宽实测点上去命中的就是链接本身，href 正常） ",
    "🔧 #120 已修（页头窄屏回正常流，不再被语言下拉压住） ",
    "🔧 #120 已做（≤768px 放弃 fixed 页头；首页头行 74–144、控件 146/218 顺序堆叠） ",
    "🔧 #119 已修（实测右上工具栏占 216px，页头 right 改 230） ",
    "🔧 #121 已修（退出按钮 fixed 到页头这一排 y=13；内容区 gap 清零，商家 tab 行从 y170 提到 y74） ",
    "🔧 #119 已修（同 32，两端用同一个 right 值） ",
    "🔧 #121 已做（按会话给「翻译成中文」按钮，译文浅色小字挂在原文下方，结果缓存；实测西语→中文） ",
    "🔧 #121 已做（红点挂在 sticky 的 tab 行，切到任何 tab 都看得见；6 秒轮询） ",
    "🔧 #121 已做（实测：转人工后红点 1 → 点「查看」消失 → 买家再说话又变 1） ",
    "❌ 误判，不是 bug（2026-11-03 复查：当地址栏也实测过，切泰语 0.5 秒内变 l=th，刷新后仍是泰语。上次是读了 Playwright 的 pg.url，它不会立刻反映 pushState，要读 location.search） ",
]

txt = io.open(PATH, encoding="utf-8").read()
fixed = 0
for pre in PREFIXES:
    while (pre + pre) in txt:
        txt = txt.replace(pre + pre, pre)
        fixed += 1
io.open(PATH, "w", encoding="utf-8", newline="\n").write(txt)
print("折叠重复前缀:", fixed, "处")

import re
for ln in txt.split("\n"):
    if re.match(r"^\|\s*(27|29|32|33|34|35|36|37|38)\s*\|", ln):
        print(ln[:150])
