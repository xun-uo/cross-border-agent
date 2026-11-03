# -*- coding: utf-8 -*-
"""把 #121 这轮的处理结果写回待修清单的状态列（只改每行第 4 格开头的状态词）。"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PATH = r"D:\跨境智服\待修清单.md"

NEW = {
    "27": "🔧 #120 已修（390 宽实测宽 132px、不再撑满整行） ",
    "28": "🔧 #120 已修（390 宽实测点上去命中的就是链接本身，href 正常） ",
    "29": "🔧 #120 已修（页头窄屏回正常流，不再被语言下拉压住） ",
    "30": "🔧 #120 已做（≤768px 放弃 fixed 页头；首页头行 74–144、控件 146/218 顺序堆叠） ",
    "32": "🔧 #119 已修（实测右上工具栏占 216px，页头 right 改 230） ",
    "33": "🔧 #121 已修（退出按钮 fixed 到页头这一排 y=13；内容区 gap 清零，商家 tab 行从 y170 提到 y74） ",
    "34": "🔧 #119 已修（同 32，两端用同一个 right 值） ",
    "35": "🔧 #121 已做（按会话给「翻译成中文」按钮，译文浅色小字挂在原文下方，结果缓存；实测西语→中文） ",
    "36": "🔧 #121 已做（红点挂在 sticky 的 tab 行，切到任何 tab 都看得见；6 秒轮询） ",
    "37": "🔧 #121 已做（实测：转人工后红点 1 → 点「查看」消失 → 买家再说话又变 1） ",
    "38": "❌ 误判，不是 bug（2026-11-03 复查：当地址栏也实测过，切泰语 0.5 秒内变 l=th，刷新后仍是泰语。上次是读了 Playwright 的 pg.url，它不会立刻反映 pushState，要读 location.search） ",
}

lines = io.open(PATH, encoding="utf-8").read().split("\n")
out = []
for ln in lines:
    m = re.match(r"^\|\s*(\d+)\s*\|", ln)
    if m and m.group(1) in NEW:
        cells = ln.split("|")
        # cells[0] 是行首空串，cells[1]=#, [2]=位置, [3]=问题, [4]=状态
        if len(cells) >= 5:
            cells[4] = " " + NEW[m.group(1)] + re.sub(r"^\s*(⬜|🔧|❌)[^（]*", "", cells[4]).strip()
            # 上面会吃掉旧状态词，保留括号里的时间与说明
            cells[4] = " " + NEW[m.group(1)] + cells[4].strip()
            ln = "|".join(cells)
    out.append(ln)

io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("已更新", len(NEW), "行")
for ln in out:
    if re.match(r"^\|\s*(26|27|33|37|38)\s*\|", ln):
        print(ln[:160])
