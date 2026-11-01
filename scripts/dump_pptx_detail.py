# -*- coding: utf-8 -*-
"""临时工具：导出指定页的 shape 细节（位置/尺寸/字号），用于安全改字。"""
import io
import sys
from pptx import Presentation
from pptx.util import Emu

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\1\Desktop\跨境智服Agent-答辩PPT-v10.pptx"
WANT = [6, 10, 11, 12, 13, 16, 19, 20]

p = Presentation(SRC)
print("slide size", Emu(p.slide_width).inches, "x", Emu(p.slide_height).inches)
for i, s in enumerate(p.slides, 1):
    if i not in WANT:
        continue
    print(f"\n=== slide {i} ===")
    for j, sh in enumerate(s.shapes):
        if not sh.has_text_frame:
            continue
        txt = " / ".join(pa.text for pa in sh.text_frame.paragraphs if pa.text.strip())
        if not txt:
            continue
        sizes = []
        for pa in sh.text_frame.paragraphs:
            for r in pa.runs:
                sz = r.font.size.pt if r.font.size else None
                sizes.append(sz)
        words = sh.text_frame.word_wrap
        print(f" [{j}] L={Emu(sh.left).inches:.2f} T={Emu(sh.top).inches:.2f} "
              f"W={Emu(sh.width).inches:.2f} H={Emu(sh.height).inches:.2f} "
              f"sz={set(sizes)} wrap={words} :: {txt[:120]}")
