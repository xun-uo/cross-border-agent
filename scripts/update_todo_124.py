# -*- coding: utf-8 -*-
"""把 #124 的结果写回待修清单 48/49/50 的状态列。"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PATH = r"D:\跨境智服\待修清单.md"
NEW = {
    "48": ("🔧 #124 已修（① 关键词兜底不再看 `intent`，只要命中 `_DO_WORDS` 就 `need_human=True`；"
           "② 新增超长规则：`len(text) >= 1500` 且出现退货/换货/退款/报修/赔偿/投诉/破损等词 → 直接 `need_human`。"
           "实测 8515 字长信连跑两次都是 `handoff=True`、回复里带「我请同事来协助您处理」；"
           "「退货政策是什么」「无理由退货是几天」仍 `handoff=False`，「能退吗」`True`） "),
    "49": ("🔧 #124 已做（按用户选的 ②：纯图没文字 → 回「图片收到了，方便补一句说明吗？（破损/漏发/尺寸不对/想退货）」"
           "并**不转人工**；图 + 文字 → 交给正常 AI 流程，文字里命中办理类词照样转人工。"
           "实测：纯图 → 有补充说明提示、无「正在等待商家回复」；图 + 「外包装破了，能退吗」→ 转人工） "),
    "50": ("🔧 #124 已修（`order = find_order(买家写的号)` 查不到就退回 `find_order(bound_order)`，"
           "并在 `intent` 上记 `_order_no_ignored`；两个都查不到 → 清空 `intent[\"order_no\"]`、记 `_order_no_not_found`，"
           "让既有的「缺订单号 → 追问」分支用固定话术问。实测四种组合：假号+已绑定→用绑定订单的真实物流回答；"
           "假号写在句首→明确回「与登录绑定的订单不一致」；假号+未绑定→固定话术「方便发一下订单号吗」；真号→正常答） "),
}

txt = io.open(PATH, encoding="utf-8").read()
out = []
changed = 0
for ln in txt.split("\n"):
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
print("总行数:", len(rows))
print("仍未修(⬜):", [re.match(r"^\|\s*(\d+)", ln).group(1) for ln in rows if "⬜" in ln.split("|")[4]])
