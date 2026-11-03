# -*- coding: utf-8 -*-
"""追加 #49：表情包/无关图片也一律转人工。"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROW = (
    "| 49 | 买家端 · 图片一律转人工（表情包也转） | 买家发了一张**表情包**（大笑的人），"
    "系统照样回「图片已收到，已转人工客服处理，请稍候。」并把会话转进商家待处理。"
    "表情包、无关图片、误发截图都算「要办事」了，人工池会被无意义的图占满，买家也收到一句过重的话 | "
    "⬜ 待确认（2026-11-03 23:17 报，商家端截图：买家 23:17 发表情包 → AI 23:17 回「已转人工」）。"
    "**现状**：`_run_image_turn()` 只要收到图片就 `mark_pending` + `enter_human`，不看有没有文字、文字说什么、"
    "也没有任何视觉判断（本地跑的是纯文本模型，看不了图）。<br>"
    "**修法候选（按成本排）**：① **图 + 文字** → 按文字走正常意图流程（已有代码路径，几乎零成本）；"
    "**纯图没文字** → 回一句「看到您发的图片了，方便补一句说明吗？（比如破损/漏发/尺寸不对）」并**不转人工**，"
    "等下一句带文字的再判断；② 文字里命中 `_DO_WORDS`（退货/破损/漏发/赔偿…）才转人工；"
    "③ 真要做「认表情包」得上多模态模型，成本和延迟都不划算，不建议。<br>"
    "**注意**：这个改动会削弱「发图＝转人工」的即时性——破损图配一句「破了」还是照样转，不用担心中间没人接。|"
)

PATH = r"D:\跨境智服\待修清单.md"
s = io.open(PATH, encoding="utf-8").read().rstrip("\n")
io.open(PATH, "w", encoding="utf-8", newline="\n").write(s + "\n" + ROW + "\n")

rows = [ln for ln in io.open(PATH, encoding="utf-8").read().split("\n")
        if re.match(r"^\|\s*\d+\s*\|", ln)]
ids = [re.match(r"^\|\s*(\d+)", ln).group(1) for ln in rows]
print("总行数:", len(rows), "| 最后编号:", ids[-1], "| 重复:", [x for x in set(ids) if ids.count(x) > 1])
