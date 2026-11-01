# -*- coding: utf-8 -*-
"""临时工具：导出 PPT 每页文本，用于核对要改的地方。"""
import io
import sys
from pptx import Presentation
from pptx.util import Emu

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\1\Desktop\跨境智服Agent-答辩PPT-v11.pptx"
DST = r"D:\跨境智服\out\ppt_dump_v11.txt"

p = Presentation(SRC)
lines = []
for i, s in enumerate(p.slides, 1):
    lines.append(f"=== slide {i} ===")
    for sh in s.shapes:
        txt = ""
        if sh.has_text_frame:
            txt = " | ".join(par.text for par in sh.text_frame.paragraphs if par.text.strip())
        if getattr(sh, "has_table", False) and sh.has_table:
            rows = []
            for r in sh.table.rows:
                rows.append(" || ".join(c.text.replace("\n", " ") for c in r.cells))
            txt = "[TABLE] " + " ;; ".join(rows)
        if not txt.strip():
            continue
        try:
            t = f"{Emu(sh.top).inches:.2f}"
            h = f"{Emu(sh.height).inches:.2f}"
        except Exception:
            t = h = "?"
        lines.append(f"  <{sh.shape_type}> top={t} h={h} :: {txt}")

open(DST, "w", encoding="utf-8").write("\n".join(lines))
print("slides:", len(p.slides), "->", DST)
