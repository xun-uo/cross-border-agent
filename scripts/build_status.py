# -*- coding: utf-8 -*-
"""生成《跨境智服 Agent · 当前完成情况》docx。

内容全部来自代码与数据的实际核对（2026-10-31），不写未实现的功能。
"""
import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

DST = r"D:\1\Desktop\跨境智服Agent-完成情况-v1.docx"
FONT = "微软雅黑"

doc = docx.Document()

# 页面与默认字体
sec = doc.sections[0]
sec.left_margin = Cm(2.4)
sec.right_margin = Cm(2.4)
sec.top_margin = Cm(2.2)
sec.bottom_margin = Cm(2.2)

normal = doc.styles["Normal"]
normal.font.name = FONT
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

for i in range(1, 4):
    st = doc.styles[f"Heading {i}"]
    st.font.name = FONT
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st.font.color.rgb = RGBColor(0x1F, 0x38, 0x64)

doc.styles["Heading 1"].font.size = Pt(15)
doc.styles["Heading 2"].font.size = Pt(12)


def para(text, style=None, bold=False, size=None):
    p = doc.add_paragraph(style=style)
    r = p.add_run(text)
    if bold:
        r.bold = True
    if size:
        r.font.size = Pt(size)
    return p


def bullet(text):
    return para(text, style="List Bullet")


def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        r = cell.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(10)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(val))
            r.font.size = Pt(10)
    if widths:
        for r_ in t.rows:
            for i, w in enumerate(widths):
                r_.cells[i].width = w
    # 行内禁止跨页：避免一行被劈成两页
    for r_ in t.rows:
        trPr = r_._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))
    doc.add_paragraph()
    return t


# ------------------------------------------------------------------ 封面
title = doc.add_paragraph()
title.alignment = 1
r = title.add_run("跨境智服 Agent · 当前完成情况")
r.bold = True
r.font.size = Pt(20)
r.font.name = FONT
r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)

sub = doc.add_paragraph()
sub.alignment = 1
r = sub.add_run("截至 2026-10-31 · 已上线公网，可实际使用")
r.font.size = Pt(11)
r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

doc.add_paragraph()

# ------------------------------------------------------------------ 一
doc.add_heading("一、一句话说清现在是什么状态", level=1)
para("系统已经跑通，不是原型截图：一个 Streamlit 应用，买家端和商家后台在同一套代码里，"
     "公网可访问。买家能提问、能看到物流进度、能转到人工；商家能在后台接管对话、改规则、看判定日志。"
     "合规判定在每条回复发出前执行，命中才改写，不命中直接放行。")

# ------------------------------------------------------------------ 二
doc.add_heading("二、已经做完的（逐项可验证）", level=1)

doc.add_heading("2.1 对话主链路", level=2)
bullet("意图识别：输出主意图 + 附加标记（投诉 / 合规敏感）+ 情绪等级 + 语言 + 是否需要人工，JSON 结构化输出。")
bullet("「问规则」与「要办事」分流：问流程、问期限、问条款 → AI 答；说要退款、要退货、要报修 → 直接转人工，不追问订单号。")
bullet("订单与物流查询：20 条 Mock 订单，覆盖在途、已签收、部分发货、物流滞留、清关扣留、丢失、退换中、已退款、已取消等 10 种状态。")
bullet("知识库检索：26 条 FAQ 与政策条目，关键词 + 同义词匹配，客服与 AI 读同一份。")
bullet("草稿生成：按目标市场注入该市场红线清单，限制模型不承诺时效、不编造订单信息。")
bullet("全链 trace：每一步的输入输出都留痕，可在界面上回放，用于演示与复盘。")

doc.add_heading("2.2 合规引擎（核心能力）", level=2)
bullet("四级流水线：切分宣称 → 语境判定 → 规则匹配 → 分级动作（L1 拦截 / L2 改写 / L3 放行）。")
bullet("规则库 44 条，覆盖 7 个市场：CN 8 条、EU 8 条、US 8 条、PH / KR / RU / MN 各 5 条。")
bullet("两类规则：禁止型（出现即违规）与条件型（出现且未满足前置条件才违规，支持跨句判断）。")
bullet("否定语境豁免：触发词落在 not / cannot / 不承诺 / 不用于 等语境里即放行，英文按词边界匹配，避免 heal 误伤 healthcare。")
bullet("语义兜底层：规则层判 pass 后，对商品咨询 / 投诉 / 合规敏感三类意图再做一次语义判定，只加判不减判。")
bullet("自动改写 + 复检：改写后的句子再过一遍判定，最多两轮，仍不过则走安全话术或转人工。")

doc.add_heading("2.3 人工接管（双向闭环）", level=2)
bullet("触发：要办类诉求、红线无法安全改写、情绪激动且涉及金额或平台处罚、明确要求转人工、连续 3 轮未收敛。")
bullet("三态会话：AI / 待人工 / 人工中，状态持久，切走后不会被 AI 抢话。")
bullet("商家在后台回复 → 买家页 4 秒轮询自动拉到，不用刷新。")
bullet("10 秒无人响应，系统自动补发一条安抚消息，只发一次，不刷屏。")
bullet("商家点「结束会话（交还 AI）」后，对话回到 AI 模式，历史完整保留。")

doc.add_heading("2.4 商家后台（5 个页签）", level=2)
bullet("待处理会话：按状态列出，点开可见完整对话与每条回复的判定依据，可直接回复。")
bullet("规则库：可视化查看与编辑、导入导出、即时生效，带版本记录与一键回滚。")
bullet("判定看板：按市场、判定结果、类目、语种、时段聚合的统计。")
bullet("会话记录：每条回复的意图、判定、命中条款、是否改写、耗时。")
bullet("商品与订单：Mock 商品 4 条、订单 20 条，可查状态与物流节点。")

doc.add_heading("2.5 界面与体验", level=2)
bullet("三语界面：中文 / 英语 / 西班牙语，回复语言跟随界面语言。")
bullet("买家端气泡带「AI」角标，人工回复不带——买家一眼能分清在跟谁说话。")
bullet("物流地图：按真实经纬度算大圆航线，节点逐个点亮，当前节点脉动，能看出卡在哪一段。")
bullet("每日使用限额、登录鉴权、debug 模式（?debug=1）看判定细节。")

# ------------------------------------------------------------------ 三
doc.add_heading("三、实测数据", level=1)
para("以下数字来自 scripts/ 下的评测脚本实际运行，可复现。", size=10)
table(
    ["指标", "实测结果", "说明"],
    [
        ["红线漏杀率", "0%（0/20）", "20 条明确违规样本全部被识别"],
        ["误杀率", "0%（0/20）", "20 条含风险词但合规的样本全部放行"],
        ["擦边识别率", "95%（19/20）", "1 条需结合商家具体政策，测试集无上下文"],
        ["主意图准确率", "90%（45/50）", "标注集比对"],
        ["全长响应延迟", "2.0 – 3.5 秒", "意图 → 工具 → 生成 → 合规全链"],
        ["追问延迟", "0.5 – 0.8 秒", "缺订单号时不生成，直接追问"],
        ["单次咨询调用数", "约 2.8 次", "含语义兜底按需触发"],
        ["功能场景通过率", "7 / 7", "七条演示脚本均按预期走完"],
    ],
    widths=[Cm(4.2), Cm(4.0), Cm(7.4)],
)
para("另有一份 15 条留出集做过盲测：第一次盲测通过 60%，按失败项改进后 15/15。"
     "改进依据来自留出集的失败项，所以 15/15 不能当作泛化能力的证明——真实水平介于两者之间。"
     "这一点如实写出，不拿它当成绩。", size=10)

# ------------------------------------------------------------------ 四
doc.add_heading("四、还没做 / 已知边界", level=1)
para("这一节是给自己和评审看的短板清单，不掩饰。", size=10)
table(
    ["项", "现状", "影响"],
    [
        ["独立 API 服务", "未做。界面直接调用引擎，没有 FastAPI 层", "无法被第三方系统集成，只能人工在页面用"],
        ["向量检索", "未接。知识库走关键词 + 同义词匹配", "问法差异大时召回率低于向量方案"],
        ["四个市场条款", "PH / KR / RU / MN 共 20 条按通用规则起草，标注「待核实」", "正式商用前必须逐条核对官方原文"],
        ["改写可用率", "未做人工评分", "缺一项指标，暂用「改写后复检通过率」代替"],
        ["会话与日志存储", "内存态，重启即清空", "Cloud 免费实例休眠后，历史会话和统计会重置"],
        ["数据", "全部为 Mock，未接真实店铺", "下单、物流、商品均为本地 JSON"],
    ],
    widths=[Cm(3.6), Cm(7.4), Cm(4.6)],
)

# ------------------------------------------------------------------ 五
doc.add_heading("五、体验入口", level=1)
table(
    ["项", "内容"],
    [
        ["访问地址", "https://cross-border-agent.streamlit.app"],
        ["买家端", "buyer / niao2026"],
        ["商家后台", "admin / niao2026"],
        ["唤醒说明", "免费实例闲置会休眠，首次打开等 30–60 秒属正常"],
        ["建议路径", "先在买家端问一单物流 → 再触发一次转人工 → 切商家后台接管 → 交还 AI"],
    ],
    widths=[Cm(3.2), Cm(12.4)],
)

# ------------------------------------------------------------------ 六
h6 = doc.add_heading("六、代码与数据规模", level=1)
h6.paragraph_format.page_break_before = True
table(
    ["部分", "内容"],
    [
        ["app/", "9 个模块：agent、compliance、semantic、handoff、judge_log、rules_store、llm、config"],
        ["web/app.py", "单文件约 1280 行：买家端、商家后台、地图、trace、鉴权、i18n"],
        ["data/", "rules.json（44 条）、kb.json（26 条）、orders.json（20 条）、products.json（4 条）"],
        ["scripts/", "22 个脚本：评测、留出盲测、语义验证、延迟测试、Mock 数据生成、回归"],
    ],
    widths=[Cm(3.0), Cm(12.6)],
)

para("说明：web/app.py 是单文件，没有拆分。这是有意的取舍——工期紧，拆文件带来的回归风险大于收益，"
     "等产品化阶段再动。", size=10)

doc.save(DST)
print("saved:", DST)
