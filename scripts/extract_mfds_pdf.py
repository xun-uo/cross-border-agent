# -*- coding: utf-8 -*-
"""从 MFDS 的《不当标示广告内容标准》PDF 里抽文本，定位相关法条。"""
import io
import sys
from pathlib import Path

from pypdf import PdfReader

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

src = Path(r"D:\跨境智服\out\mfds_gf_label.pdf")
r = PdfReader(str(src))
print("页数:", len(r.pages))
pages = []
for i, pg in enumerate(r.pages):
    try:
        pages.append(pg.extract_text() or "")
    except Exception as e:
        pages.append("")
        print("  第%d页抽取失败: %s" % (i + 1, e))

full = "\n".join(pages)
out = Path(r"D:\跨境智服\out\mfds_gf_label.txt")
out.write_text(full, encoding="utf-8")
print("提取字符数:", len(full), "->", out)

KWS = ["제8조", "제1호", "질병의 예방", "질병의 예방 및 치료", "의약품으로 오인",
       "건강기능식품", "기능성"]
for kw in KWS:
    idx = full.find(kw)
    print("\n" + "=" * 60)
    if idx < 0:
        print("未命中:", kw)
        continue
    print("命中:", kw)
    print(full[max(0, idx - 200):idx + 500].replace("\n", " "))
