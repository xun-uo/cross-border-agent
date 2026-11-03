# -*- coding: utf-8 -*-
"""把 #122 的结果写回待修清单 39–44 的状态列。"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PATH = r"D:\跨境智服\待修清单.md"
NEW = {
    "39": "🔧 #122 已修（语言下拉 + 退出登录收进同一个 `topbar_right` 容器，CSS 摆成一行；390 宽实测：下拉 x=12 y=60 w=138、退出 x=296 y=64 —— 同一排） ",
    "40": "🔧 #122 已做（图下一行「📍 现在到哪了：<最新节点> · 时间」，再加「🔍 点开放大」按钮 → `@st.dialog` 大图 + 现在到哪 + 完整轨迹；实测按钮/弹窗/时间线都在） ",
    "41": "🔧 #122 已修（窄屏页头恢复 fixed：第 1 条 0–56px 店名/在线/当前订单、右侧留 130px 给平台工具栏；第 2 条 60–100px 语言+退出；内容从 106px 开始；tab 行 sticky top:104） ",
    "42": "🔧 #122 已做（`handoff.by_order()` 按订单号找回最近会话，`_after_login()` 买家分支沿用旧 sid；实测 sid `d8580ad3d8` 退出重登后不变、2 条记录都在；服务重启后自然新建，符合约定） ",
    "43": "🔧 #122 已修（根因是 `generate_draft` 无条件把整份订单 JSON 塞进 prompt。改成 `_order_brief()` 按意图裁剪——非物流意图只给订单号+商品、一个物流字段都不给，并在系统提示里加第 6 条「只回答被问的，别人问功效别报物流」。实测：「能去黑头吗」「那能干嘛」回复里 0 个物流词；「我的订单在哪」照常给承运商/运单号/预计送达） ",
    "44": "🔧 #122 已修（新增 `app/clock.py`，固定 UTC+8、不依赖容器 tzdata；`web/app.py:_now()`、`handoff._now()`、`judge_log` 时间戳全部改走它。实测本地时间 21:55 → 气泡 21:55；线上容器是 UTC，会上报北京时间） ",
}

lines = io.open(PATH, encoding="utf-8").read().split("\n")
out = []
changed = 0
for ln in lines:
    m = re.match(r"^\|\s*(\d+)\s*\|", ln)
    if m and m.group(1) in NEW:
        cells = ln.split("|")
        if len(cells) >= 5:
            cells[4] = " " + NEW[m.group(1)] + re.sub(r"^\s*⬜[^（]*", "", cells[4]).strip()
            ln = "|".join(cells)
            changed += 1
    out.append(ln)

io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("更新行数:", changed)
for ln in out:
    if re.match(r"^\|\s*(39|41|44)\s*\|", ln):
        print(ln[:150])
