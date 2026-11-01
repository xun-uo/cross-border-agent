# -*- coding: utf-8 -*-
"""v11 → v12：加入越南语 / 泰语 / 印尼语之后，更新 PPT 里描述语种的地方。

只改事实描述，不动排版。
"""
import copy
import io
import sys

from pptx import Presentation
from pptx.oxml.ns import qn

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\1\Desktop\跨境智服Agent-答辩PPT-v11.pptx"
DST = r"D:\1\Desktop\跨境智服Agent-答辩PPT-v12.pptx"


def rewrite(tf, texts):
    paras = list(tf.paragraphs)
    tmpl = copy.deepcopy(paras[0]._p)
    body = tf._txBody
    for p in paras:
        body.remove(p._p)
    for br in tmpl.findall(qn("a:br")):
        tmpl.remove(br)
    for t in texts:
        newp = copy.deepcopy(tmpl)
        runs = newp.findall(qn("a:r"))
        for r in runs[1:]:
            newp.remove(r)
        if runs:
            run = runs[0]
            ts = run.findall(qn("a:t"))
            for extra in ts[1:]:
                run.remove(extra)
            if ts:
                ts[0].text = t
            else:
                el = run.makeelement(qn("a:t"), {})
                el.text = t
                run.append(el)
        body.append(newp)


def find(slide, needle):
    hits = [sh for sh in slide.shapes
            if sh.has_text_frame and needle in sh.text_frame.text]
    assert len(hits) == 1, f"{needle!r} matched {len(hits)}"
    return hits[0]


prs = Presentation(SRC)
S = list(prs.slides)

# ---- 第 19 页：已知短板里的语种 ----
short = find(S[18], "语种")
old = short.text_frame.text
print("原文本:\n" + old)
lines = []
for ln in old.split("\n"):
    if "语种" in ln:
        lines.append("· 语种 中 / 英 / 西 / 越 / 泰 / 印尼，德法预留")
    else:
        lines.append(ln)
rewrite(short.text_frame, lines)
print("新文本:\n" + "\n".join(lines))

# ---- 第 3 页副标题里若有语种描述，一并改 ----
# ---- 第 2 页：痛点里的语种（原文有错字「术昼」，且语种和现在不符） ----
try:
    pain = find(S[1], "人工翻译成本高")
    print("slide2 原文:", pain.text_frame.text)
    rewrite(pain.text_frame, ["英、西、越、泰、印等语种昼夜咨询，人工翻译成本高，夜间容易漏回"])
    print("slide2 新文:", pain.text_frame.text)
except AssertionError as e:
    print("slide2 未改:", e)

for i, s in enumerate(S):
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        txt = sh.text_frame.text
        if "en / es" in txt or "en/es" in txt:
            print(f"slide {i+1} 含 en/es：{txt[:80]}")

prs.save(DST)
print("saved:", DST)
