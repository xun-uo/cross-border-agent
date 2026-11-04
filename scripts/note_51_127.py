# -*- coding: utf-8 -*-
"""给 #51 的已修说明补上 #127 的三态细分。"""
import io
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PATH = r"D:\跨境智服\待修清单.md"
ADD = ("**（#127 补）**用户指出「商家还没接入却写已接入」—— 现在按 `owner` 再分一档："
       "刚转人工没人回 →「👤 已转人工 · 等待客服接入」；客服首次回复后 →「👤 人工客服已接入 · admin」。"
       "三态实测：AI / 等待接入 / 已接入都正确。")

txt = io.open(PATH, encoding="utf-8").read()
out = []
hit = False
for ln in txt.split("\n"):
    m = re.match(r"^\|\s*51\s*\|", ln)
    if m and not hit:
        cells = ln.split("|")
        # cells[4] 是状态格，末尾（倒数第二段才是内容，最后一个空串是行尾）
        cells[4] = cells[4].rstrip() .rstrip("）") + "），" + ADD + " "
        ln = "|".join(cells)
        hit = True
    out.append(ln)
io.open(PATH, "w", encoding="utf-8", newline="\n").write("\n".join(out))
print("是否更新 #51:", hit)
row51 = [ln for ln in out if re.match(r"^\|\s*51\s*\|", ln)]
print(row51[0][-260:] if row51 else "无")
