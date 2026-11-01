# -*- coding: utf-8 -*-
"""v12 → v13：市场从 7 个扩到 9 个（+英国、+日本）、规则 59 条、订单 34 单、
知识库 40 条，并修正 P10 的商家账号写法。只改事实描述，不动排版。
"""
import copy
import io
import sys

from pptx import Presentation
from pptx.oxml.ns import qn

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\1\Desktop\跨境智服Agent-答辩PPT-v12.pptx"
DST = r"D:\1\Desktop\跨境智服Agent-答辩PPT-v13.pptx"


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
    assert len(hits) == 1, "「%s」匹配到 %d 个 shape" % (needle, len(hits))
    return hits[0]


def line_replace(slide, needle, fn):
    sh = find(slide, needle)
    old = sh.text_frame.text
    lines = [fn(ln) if needle in ln else ln for ln in old.split("\n")]
    rewrite(sh.text_frame, lines)
    print("  改后:", " | ".join(lines)[:110])


prs = Presentation(SRC)
S = list(prs.slides)

print("P6 规则结构")
line_replace(S[5], "共 44 条规则", lambda ln: (
    "共 59 条规则，覆盖 9 个市场：美国 / 欧盟 / 英国 / 日本 / 韩国 / 中国 / 菲律宾 / 俄罗斯 / 蒙古。"
    "其中 39 条已逐条核对官方原文，其余 20 条明确标注「待核实」。"))

print("P10 账号")
line_replace(S[9], "xinghe2026", lambda ln: (
    "商家 admin / niao2026　　买家 ORDER20261021001 · 手机尾号 0001"))

print("P11 规模数字")
line_replace(S[10], "26 条知识条目", lambda ln: (
    "59 条规则 · 40 条知识条目 · 34 条订单 · 60 条评测集"))

print("P19 短板")
line_replace(S[18], "条款编号需逐条核对", lambda ln: (
    "· 39 / 59 条条款已核对官方原文，其余 20 条待核"))

print("P19 下一步")
line_replace(S[18], "下一步最该做", lambda ln: (
    "下一步最该做的一件事：把剩余 20 条示例条款核对到官方原文，并接入一家真实店铺的订单接口。"))

prs.save(DST)
print("\nsaved:", DST)

# 校验
chk = Presentation(DST)
for i in (1, 5, 9, 10, 18):
    print("\n--- P%d ---" % (i + 1))
    for sh in chk.slides[i].shapes:
        if sh.has_text_frame and ("规则" in sh.text_frame.text or "24" in sh.text_frame.text
                                  or "admin" in sh.text_frame.text or "下一步" in sh.text_frame.text):
            print(sh.text_frame.text.replace("\n", " | ")[:220])
