# -*- coding: utf-8 -*-
"""把 #123 的结果写回待修清单 46/47 的状态列。"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PATH = r"D:\跨境智服\待修清单.md"
NEW = {
    "46": ("🔧 #123 已修（① 「处理中」改成贴输入框上方的固定小条 `.busy-pill`，"
           "实测 y=796–828、输入框 836，不重叠也不会被气泡滚出视口；"
           "② 重复发送随①缓解，没有再改输入框；"
           "③ `generate_draft` 的订单资料里加「买家已绑定本单，不要再问订单号」+ 系统提示第 7 条，"
           "实测「我要退货」「我拆封了…能退吗」都不再问订单号；"
           "④ 拼转人工提示前 `rstrip(\" ·•-*—–\")`，实测回复里没有孤立符号行了。"
           "另外把「能退吗/能不能退/怎么退/能换吗」加进 `_DO_WORDS` 兜底："
           "实测这类「要办」的问法现在会转人工，纯政策问题（退货政策是什么 / 无理由退货是几天）仍由 AI 直答） "),
    "47": ("🔧 #123 已修（`mark_pending()` / `enter_human()` 改成「只要不是 pending 就置 pending」，"
           "并重置 `pending_since`、`comforted`（否则上一轮的安抚计时会让「人工客服还没回复」立刻蹦出来）。"
           "实测：第一次转人工 → 未回复(1) → 点「结束会话（交还 AI）」→ 会话移出列表 → 买家再次触发人工 → "
           "未回复(1)、已回复(0)，红点和分组一致了） "),
}

txt = io.open(PATH, encoding="utf-8").read()
lines = txt.split("\n")
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
rows = [ln for ln in out if re.match(r"^\|\s*\d+\s*\|", ln)]
ids = [re.match(r"^\|\s*(\d+)", ln).group(1) for ln in rows]
print("总行数:", len(rows), "| 未修(⬜):", sum(1 for ln in rows if "⬜" in ln.split("|")[4]))
for ln in out:
    if re.match(r"^\|\s*(46|47)\s*\|", ln):
        print(ln[:110])
