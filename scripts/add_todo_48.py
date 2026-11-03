# -*- coding: utf-8 -*-
"""追加 #48：超长/多主题输入的转人工判据不稳定。"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROW = (
    "| 48 | 买家端 · 超长/多主题输入的转人工判据不稳定 | "
    "同一段 8515 字符的长投诉信：**线上截图那次没转人工**"
    "（回复只有政策+流程+材料清单，没有「我请同事来协助您处理」）；"
    "**我本地同一条文本跑出的是** `return_exchange` + `need_human=True` + `handoff=True`"
    "（回复 817 字，带转人工提示） | "
    "⬜ 待观察（2026-11-03 23:17 报）。**结论**：超长文本本身处理没问题（没崩、没超时、结构清晰），"
    "问题在**意图判定会飘**：一条消息里同时有退货、物流、清关、产品不适、赔偿、投诉六个主题时，"
    "分类结果在 `return_exchange` / `complaint` / `product_inquiry` 之间摆动，"
    "而 `need_human` 的关键词兜底只在 `intent in (return_exchange, complaint)` 时才生效 —— "
    "判成 product_inquiry 就漏转。<br>"
    "**修法候选**：① 长度 > 1500 字且含办理类词（退/换/修/赔/投诉）→ **跳过意图分类直接转人工**"
    "（最稳，也符合「要办的事一律转人工」）；② 关键词兜底不再看 intent，只看文本是否命中 `_DO_WORDS`；"
    "③ 长文本先摘要再分类（多一次模型调用）。倾向 ①+②，成本最低。<br>"
    "**注意**：别把「问政策的短问题」也卷进去（「退货政策是什么」必须仍由 AI 直答，实测 #123 已能区分）。|"
)

PATH = r"D:\跨境智服\待修清单.md"
s = io.open(PATH, encoding="utf-8").read().rstrip("\n")
io.open(PATH, "w", encoding="utf-8", newline="\n").write(s + "\n" + ROW + "\n")

rows = [ln for ln in io.open(PATH, encoding="utf-8").read().split("\n")
        if re.match(r"^\|\s*\d+\s*\|", ln)]
ids = [re.match(r"^\|\s*(\d+)", ln).group(1) for ln in rows]
print("总行数:", len(rows), "| 最后一个编号:", ids[-1], "| 重复:", [x for x in set(ids) if ids.count(x) > 1])
