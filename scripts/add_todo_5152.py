# -*- coding: utf-8 -*-
"""追加 #51（页头不区分 AI/人工）与 #52（人工模式下 AI 仍在回话，待观察）。"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROWS = [
    (
        "| 51 | 买家端 · 页头状态不区分 AI / 人工 | 页头一直写「🟢 在线」，"
        "**AI 在服务和人已经接手，看起来一模一样**，买家分不清现在是谁在回 | "
        "🔧 #126 已修（按会话 `mode` 切换：AI →「🤖 AI 客服在线」，"
        "人工 →「👤 人工客服已接入 · <接管客服>」，人工状态加暖橙色 `is-human` 类。"
        "文案六语都给了（`_STATUS_LABELS`）。实测同一页：转人工前「🤖 AI 客服在线」、"
        "转人工后「👤 人工客服已接入」且命中 `.shop-online.is-human`） |"
    ),
    (
        "| 52 | 买家端 · 人工模式下 AI 仍在回话（间歇） | 用户截图：先发「人工」→ AI 回「我请同事来协助您处理」，"
        "紧接着发「你好」→ **AI 又回了「您好，请问有什么可以帮您？」**，说明人工模式没拦住 | "
        "⬜ 待观察（2026-11-04 16:30 线上截图）。**本地 #125 用同一串操作复现不出来**："
        "「人工」→ 有「我请同事」+ 等待文案；「你好」→ 只存消息、不产生 AI 回复，气泡列表里只有买家那句。"
        "所以不是代码路径的常态 bug。<br>"
        "**怀疑**：① 那一分钟里 Streamlit Cloud 实例重启过（内存会话全没），`handoff.is_human_mode(sid)` 变 False → 走 AI；"
        "② 买家页刷新后 sid 变了（`login_gate` 只认 URL 里的 `l`/`sid`，换了 tab 或重开可能拿到新 sid）；"
        "③ 前端把第二轮 rerun 拼到了旧状态上。<br>"
        "**下次复现要记的三件事**：买家页 URL 里的 `sid`、商家后台还能不能看到这个会话、"
        "「你好」那条回复上面有没有「已转人工，正在等待商家回复…」的提示。有这三样就能定性 |"
    ),
]

PATH = r"D:\跨境智服\待修清单.md"
s = io.open(PATH, encoding="utf-8").read().rstrip("\n")
io.open(PATH, "w", encoding="utf-8", newline="\n").write(
    s + "\n" + "\n".join(ROWS) + "\n")

rows = [ln for ln in io.open(PATH, encoding="utf-8").read().split("\n")
        if re.match(r"^\|\s*\d+\s*\|", ln)]
ids = [re.match(r"^\|\s*(\d+)", ln).group(1) for ln in rows]
print("总行数:", len(rows), "| 最后编号:", ids[-1], "| 重复:", [x for x in set(ids) if ids.count(x) > 1])
