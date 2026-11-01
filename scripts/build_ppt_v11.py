# -*- coding: utf-8 -*-
"""把 v10 里过时的数字与说明更新为线上实际状态，输出 v11。

改动依据（都已在代码/数据里核对）：
- data/rules.json          44 条（CN/EU/US 各 8，PH/KR/RU/MN 各 5）
- data/kb.json             26 条
- data/orders.json         20 条
- data/testset.json        60 条（红线 20 + 擦边 20 + 陷阱 20）
- app/agent.py retrieve_kb 关键词重叠打分，非向量检索
- 账号体系：买家 = 订单号 + 手机后四位；商家 = 账号 / 密码
"""
import copy
import io
import sys

from pptx import Presentation
from pptx.util import Inches
from pptx.oxml.ns import qn

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = r"D:\1\Desktop\跨境智服Agent-答辩PPT-v10.pptx"
DST = r"D:\1\Desktop\跨境智服Agent-答辩PPT-v11.pptx"


def rewrite(tf, texts):
    """用第一段的段落格式 + 第一个 run 的字符格式，把文本框重写成 texts。"""
    paras = list(tf.paragraphs)
    tmpl = copy.deepcopy(paras[0]._p)
    body = tf._txBody
    for p in paras:
        body.remove(p._p)

    # 模板里若带软换行，逐段复制会多出空行，先清掉
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


def shape_at(slide, idx):
    return slide.shapes[idx]


def find_shape(slide, needle):
    """按文本片段定位文本框，避免依赖 shape 序号。"""
    hits = [sh for sh in slide.shapes
            if sh.has_text_frame and needle in sh.text_frame.text]
    assert len(hits) == 1, f"{needle!r} matched {len(hits)} shapes"
    return hits[0]


prs = Presentation(SRC)
S = list(prs.slides)

# ---------- slide 1 · 封面日期 ----------
rewrite(find_shape(S[0], "2026 年 10 月").text_frame, [
    "第二届全国人工智能应用创新大赛　·　2026 年 11 月"
])

# ---------- slide 4 · 延迟口径与 slide 13 对齐 ----------
rewrite(find_shape(S[3], "全程 2–3 秒").text_frame, [
    "实测：意图 1.0s ＋ 生成 1.2s ＋ 合规 0ms，全程 2–3.5 秒"
])

# ---------- slide 6 · 规则总条数 ----------
rewrite(S[5].shapes[79].text_frame, [
    "共 44 条规则（CN / EU / US 各 8 条，PH / KR / RU / MN 各 5 条）。条款编号为技术示例，正式稿逐条核对官方原文。"
])

# ---------- slide 10 · 账号说明（双角色） ----------
rewrite(S[9].shapes[12].text_frame, [
    "商家 judge / xinghe2026　　买家 ORDER20261021001 · 手机尾号 0001"
])
rewrite(S[9].shapes[22].text_frame, ["双角色登录 + 限额"])

# ---------- slide 11 · 数据层 + 能力层 + 核心模块 ----------
rewrite(find_shape(S[10], "24 条规则").text_frame, [
    "44 条规则 · 26 条知识条目 · 20 条订单 · 60 条评测集"
])
rewrite(find_shape(S[10], "意图识别 / 订单工具").text_frame, [
    "意图识别 / 订单工具 / 知识检索 / 合规引擎 / 改写复检 / 人工接管"
])

# 右侧模块卡片只有 4 张，保持 4 行，只更新内容
s11 = S[10]
mods = [sh for sh in s11.shapes
        if sh.has_text_frame and abs(sh.left.inches - 9.05) < 0.02]
mods.sort(key=lambda sh: sh.top.inches)
assert len(mods) == 4, f"expect 4 module boxes, got {len(mods)}"

MODULE_LINES = [
    "agent.py　　　　主链路",
    "compliance.py　合规流水线",
    "handoff.py　　　人工接管",
    "web/app.py　　　买家端 + 商家后台",
]
for sh, line in zip(mods, MODULE_LINES):
    rewrite(sh.text_frame, [line])

# ---------- slide 12 · 知识检索方式 ----------
rewrite(S[11].shapes[36].text_frame, ["手册与政策 → 关键词检索"])
rewrite(S[11].shapes[38].text_frame, ["26 条手册关键词重叠就够，不上向量库省依赖"])

# ---------- slide 13 · 延迟与调用次数 ----------
rewrite(S[12].shapes[27].text_frame, [
    "全程 2–3.5 秒（意图 1.0s ＋ 生成 1.2s ＋ 合规 0ms）"
])
rewrite(S[12].shapes[30].text_frame, [
    "平均 2.8 次模型调用，单次约 1100 输入 tokens"
])

# ---------- slide 16 · 成本 ----------
rewrite(S[15].shapes[20].text_frame, [
    "平均 2.8 次调用 / 约 1100 tokens，单次咨询成本在分以内"
])

# ---------- slide 19 · 已知短板 ----------
rewrite(S[18].shapes[16].text_frame, [
    "· 规则层依赖表述模式，",
    "  未覆盖的修辞仍可能漏判",
    "· 语义兜底已落地，",
    "  但只覆盖高风险表述",
    "· 条款编号需逐条核对官方原文",
    "· 数据为 Mock，未接入真实平台",
    "· 语种 中 / 英 / 西，德 / 法预留",
    "· 注册与多租户未做，",
    "  演示账号为直给",
])
rewrite(S[18].shapes[17].text_frame, [
    "下一步最该做的一件事：把 44 条规则逐条核对官方原文，并接入一家真实店铺的订单接口。"
])

# ---------- slide 20 · 结尾账号 ----------
rewrite(S[19].shapes[8].text_frame, [
    "在线体验　cross-border-agent.streamlit.app",
    "商家 judge / xinghe2026　买家 ORDER20261021001 · 手机尾号 0001",
    "代码与规则表　github.com/xun-uo/cross-border-agent",
])

prs.save(DST)
print("saved:", DST)
