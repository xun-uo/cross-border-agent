# -*- coding: utf-8 -*-
"""v7 → v8：市场 7→9（+英国、+日本）、规则 59 条（39 已核）、订单 34 单、
知识库 40 条，并把海关总署的市场数据补进 B.2。
"""
import io
import shutil
import sys
from pathlib import Path

from docx import Document

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SRC = Path(r"D:\1\Desktop\跨境智服Agent-作品计划书-v7.docx")
DST = Path(r"D:\1\Desktop\跨境智服Agent-作品计划书-v8.docx")
shutil.copy(SRC, DST)

d = Document(str(DST))


def set_text(p, text):
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    for r in p.runs[1:]:
        r.text = ""


def set_cell(cell, text):
    p = cell.paragraphs[0]
    set_text(p, text)
    for extra in cell.paragraphs[1:]:
        set_text(extra, "")


P = d.paragraphs
REPL = {
    4: ("本稿为 v8（2026-11-01），在 v7 基础上对齐实际进展。与 v7 相比的实质变化："
        "① 市场从 7 个扩到 9 个，新增英国、日本——按海关总署 2024 年数据，英国是第二大"
        "出口目的国（11.7%），此前缺失；日本与韩国监管逻辑相近，补齐避免同质市场只做一个；"
        "② 规则库从 49 条扩到 59 条，已逐条核对官方原文的从 29 条增至 39 条（新增英国 CAP Code、"
        "日本薬機法/景品表示法/特商法各 5 条）；③ Mock 订单从 30 条扩到 34 条，覆盖全部 9 个市场；"
        "④ 知识库从 26 条扩到 40 条，五国与英日的退货、清关条目补齐；"
        "⑤ 补入海关总署的跨境电商出口规模与目的国占比数据，替换原先的市场规模留白。"),
    28: ("回复语言跟随买家界面语言：中文 / 英语 / 西班牙语 / 越南语 / 泰语 / 印尼语六种"
         "（纯订单号这类消息沿用上一轮的语种）。切换界面语言时，历史中 AI 说过的回复会批量重译为"
         "新语言，买家自己说过的话保持原样。规则库覆盖 9 个市场——美国、欧盟、英国、日本、韩国、"
         "中国、菲律宾、俄罗斯、蒙古，共 59 条规则，其中 39 条已对照官方原文核对并注明条款号。"),
    30: ("34 条 Mock 订单，覆盖美国 10 单、欧盟 8 单、拉美 2 单，以及英国、日本、菲律宾、韩国、"
         "俄罗斯、蒙古、中国各 2 单。状态覆盖：在途、已签收、待发货可取消、多件部分发货、物流滞留、"
         "清关扣留、派送异常、物流丢失、退换处理中、已退款、已取消。"),
    55: ("规则库现有 59 条：其中 39 条（中国 / 欧盟 / 美国共 27 条，英国 5 条、日本 5 条、"
         "韩国补充剂 2 条）已逐条核对官方原文并注明条款号；其余 20 条为菲律宾 / 韩国 / 俄罗斯 / "
         "蒙古的示例条款，在数据中以「待核实」显式标注。引错法条比不写更扣分，因此不做模糊表述。"),
    128: ("条款准确性：中国 / 欧盟 / 美国共 27 条、英国 5 条、日本 5 条、韩国补充剂 2 条，"
          "合计 39 条已逐条核对官方原文；菲律宾 / 韩国 / 俄罗斯 / 蒙古共 20 条为示例条款，"
          "已在数据中显式标注「待核实」，未对外宣称已核对。"),
    164: ("据海关总署数据，2024 年我国跨境电商出口约 2.15 万亿元，同比增长 16.9%，"
          "占货物贸易出口总值的 8.5%；跨境电商出口的主要目的国为美国 36.2%、英国 11.7%、"
          "德国 5.7%，出口消费品占 97.5%。本作品的 9 个市场覆盖了其中前三大目的国中的两个"
          "（美国、英国），德国由「欧盟」规则集覆盖。中小卖家的具体数量与付费意愿仍缺可查证口径，"
          "本节不填估算数字。"),
}
for idx, txt in REPL.items():
    set_text(P[idx], txt)
    print("段落 %-3d 已替换" % idx)

T = d.tables
set_cell(T[0].rows[2].cells[2],
         "合规四级流水线 + 语义兜底层 + 59 条结构化规则（39 条已核对条款）+ 条款出处")

# 表2 市场话术表：补英国、日本两行
t2 = T[2]
r = t2.add_row()
set_cell(r.cells[0], "UK")
set_cell(r.cells[1], "英语")
set_cell(r.cells[2], "直接、礼貌；价格是否含税必须写明")
set_cell(r.cells[3], "CAP Code 医疗宣称限制；14 天冷静期；UKCA / MHRA")
r2 = t2.add_row()
set_cell(r2.cells[0], "JP")
set_cell(r2.cells[1], "日语")
set_cell(r2.cells[2], "敬语；避免断言式表达")
set_cell(r2.cells[3], "薬機法 56 项功效范围；景品表示法；特商法返品特约")
print("表2 已加 UK / JP 两行")

d.save(str(DST))
print("已保存:", DST)

chk = Document(str(DST))
print("\n=== 校验 ===")
for i in (4, 28, 30, 55, 128, 164):
    print("[%d] %s..." % (i, chk.paragraphs[i].text[:72]))
t = chk.tables[2]
print("表2 现有 %d 行，末两行：" % len(t.rows))
for row in t.rows[-2:]:
    print("  ", " | ".join(c.text[:26] for c in row.cells))
