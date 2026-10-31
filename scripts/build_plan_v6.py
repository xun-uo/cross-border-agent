# -*- coding: utf-8 -*-
"""生成《跨境智服 Agent 作品计划书》v6。

在 v5 基础上对齐 2026-10-31 的实际进展：
  1) 语义兜底层已落地（v5 写的是「本次未实施」）
  2) 规则库 3 市场 24 条 -> 7 市场 44 条；语种中/英/西
  3) 人工接管从单向打标 -> 双向闭环 + 商家后台
  4) 判定日志看板、知识库 26 条
  5) 效果指标按最新实测更新
  6) 工期表：11/01-11/03 整段留出做产品化打磨（用户 2026-10-31 指定）

只改文本，不动版式：先做段落/表格文本替换，最后插入新段落。
"""
import copy
import sys

import docx
from docx.shared import Cm

SRC = r"D:\1\Desktop\跨境智服Agent-作品计划书-v5.docx"
DST = r"D:\1\Desktop\跨境智服Agent-作品计划书-v6.docx"

d = docx.Document(SRC)
P = d.paragraphs
errors = []


def set_para(idx, expect_prefix, text):
    p = P[idx]
    cur = p.text.strip()
    if not cur.startswith(expect_prefix):
        errors.append(f"[{idx}] 期望 {expect_prefix!r}，实际 {cur[:40]!r}")
        return
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(text)


def set_cell(cell, text):
    ps = cell.paragraphs
    p = ps[0]
    if p.runs:
        p.runs[0].text = text
        for r in p.runs[1:]:
            r._element.getparent().remove(r._element)
    else:
        p.add_run(text)
    for extra in ps[1:]:
        extra._element.getparent().remove(extra._element)


def add_row(tbl):
    tr = copy.deepcopy(tbl.rows[-1]._tr)
    tbl._tbl.append(tr)
    return tbl.rows[-1]


def insert_before(anchor, text, style="Normal"):
    return anchor.insert_paragraph_before(text, style=style)


# ---------------------------------------------------------------- 段落替换
set_para(2, "第二届全国人工智能应用创新大赛",
         "第二届全国人工智能应用创新大赛  ·  作品计划书  ·  2026-10-31")

set_para(4, "本稿在《作品名称》基础上",
         "本稿为 v6（2026-10-31），在 v5 基础上对齐实际进展。与 v5 相比的实质变化："
         "① 合规链路在四级流水线之后补上「语义兜底层」，规则未命中时对高风险意图做二次判定；"
         "② 规则库从 3 个市场 24 条扩到 7 个市场 44 条，回复语言增至中文 / 英语 / 西班牙语三语；"
         "③ 人工接管从「单向打标入队」升级为双向闭环，并配套商家后台；"
         "④ 效果指标按 2026-10-31 的最新实测更新。")

set_para(5, "第七节演示脚本与第八节指标中的实测值",
         "第七节演示脚本与第八节指标中的实测值，均来自 2026-10-31 的实际运行，可复现；"
         "评测脚本与留出集记录在 scripts/ 下。")

set_para(7, "一句话定位",
         "一句话定位：一个用买家语言回答物流、退换货、商品问题，并在每条回复发出前按「目标市场 + 商品品类」"
         "完成合规判定、自动改写违规表述的 AI 客服智能体；商家侧配套一个后台，能看到每条回复的判定依据，"
         "也能随时接管对话。")

set_para(9, "两个模式，主次分明", "三种使用形态，主次分明：")

set_para(27, "首发语种为英语",
         "回复语言跟随买家界面语言：中文 / 英语 / 西班牙语三语（纯订单号这类消息沿用上一轮的语种）。"
         "规则库覆盖 7 个市场——中国、欧盟、美国、菲律宾、韩国、俄罗斯、蒙古，共 44 条规则。"
         "目的不是铺语种数量，而是证明「同一套规则引擎能按市场切换」。")

set_para(35, "依据售后政策判断",
         "依据售后政策判断：是否在期限内、是否需照片证据、是否可补发或退款、是否需转人工。"
         "政策口径来自知识库，客服与系统共用同一份，避免各说各话。")

set_para(59, "4.5 人工接管", "4.5 人工接管（双向闭环）")

set_para(60, "触发条件（满足任一）",
         "触发条件（满足任一）：① 买家要「办事」而不是「问规则」——退货、换货、报修、退款、赔偿类诉求"
         "一律直接转人工，不再追问订单号；② 红线判定且无法安全改写为自然话术；"
         "③ 情绪愤怒且涉及金额争议或平台处罚；④ 买家明确要求转人工；⑤ 连续 3 轮未收敛。")

set_para(61, "动作：给买家一句安抚话术",
         "闭环链路：买家侧收到一句安抚话术（不承诺时效与结果）→ 会话状态切为「人工」→ 商家后台实时看到"
         "该会话并可回复 → 买家页 4 秒轮询拉取人工回复 → 10 秒内无人响应自动补发一条安抚消息"
         "（只发一次，不刷屏）→ 商家处理完毕点「结束会话（交还 AI）」，会话回到 AI 模式。"
         "转人工不是终点，是另一条通路的起点。")

set_para(95, "指标成对给出",
         "指标成对给出，不单边报拦截率。下表「当前实测」为 2026-10-31 实际运行结果。")

set_para(97, "“待测”是按计划必须补齐的项",
         "评测集（红线 20 / 擦边 20 / 含词合规 20，共 60 条）已全部生成并跑完，见附录 A。"
         "原初稿的「人工客服工作量下降 30%」因无基线，已删除。")

set_para(99, "实测：一次完整咨询消耗",
         "实测：一次完整咨询平均约 2.8 次模型调用。意图识别约 200 输入 tokens；草稿生成约 900 输入 / "
         "300 输出 tokens；合规改写按需触发；语义兜底层只在规则层放行且意图属高风险时才调用。"
         "按所选模型的计费单价折算，单条咨询成本可控制在分以内，具体单价以模型厂商当期价格为准。")

set_para(110, "原分工中的前端与文档岗位",
         "原分工中的前端与文档岗位因人员变动已取消，对应工作由技术侧承担；工期表按单人节奏重排，"
         "已砍掉非必要范围（多语种铺量、真实平台对接）。11-01 至 11-03 三天集中用于产品化打磨"
         "（界面交互、异常态、联调与回归）——这是评审能直接感知的部分，优先级高于继续扩功能。")

set_para(112, "条款准确性",
         "条款准确性：CN / EU / US 三个市场共 24 条已逐条核对官方原文；PH / KR / RU / MN 共 20 条"
         "按当地平台通用规则与法规起草，已标注「待核实」，正式商用前须逐条核对。")

set_para(114, "语种只做两种",
         "语种只做三种：中文 / 英语 / 西班牙语。多语言能力靠话术规范表体现，不靠语种数量堆。")

set_para(120, "补测时间：2026-10-27",
         "主集与留出集补测时间：2026-10-27；语义兜底层与人工闭环相关能力的补测时间：2026-10-31。"
         "数据由 scripts/eval.py 与 scripts/holdout.py 生成，可复现。")

set_para(139, "补齐路径是加一层 LLM 语义兜底",
         "补齐路径是加一层 LLM 语义兜底：规则层判为 pass 时，对商品咨询 / 投诉 / 合规敏感三类意图再做一次"
         "语义判定。该层只做「加判」不做「减判」——规则层判定过的一律不改，避免把已经正确的拦截推翻。"
         "这层已于 2026-10-28 落地。")

set_para(150, "实测数据：一次完整咨询 = 2 次模型调用",
         "实测数据：一次完整咨询平均约 2.8 次模型调用；合规规则匹配与语义兜底判定在本地完成，"
         "规则层不产生模型调用成本。")

# ---------------------------------------------------------------- 表格替换
# TABLE 0 痛点表：同步更新规则数与语种
t0 = d.tables[0]
set_cell(t0.rows[1].cells[1], "买家使用英、西、德、法、韩、俄等多种语言；夜间与周末咨询无人值守，人工翻译成本高")
set_cell(t0.rows[1].cells[2], "按买家语言直接生成（中 / 英 / 西三语已实现），非翻译链路")
set_cell(t0.rows[2].cells[2], "合规四级流水线 + 语义兜底层 + 44 条结构化规则 + 条款出处")

# TABLE 2 市场话术表：3 行 -> 4 行
t2 = d.tables[2]
set_cell(t2.rows[1].cells[0], "CN")
set_cell(t2.rows[1].cells[1], "中文")
set_cell(t2.rows[1].cells[2], "正式称呼「您」；不主动承诺时效")
set_cell(t2.rows[1].cells[3], "广告法：绝对化用语、非医疗品疾病宣称")

set_cell(t2.rows[2].cells[0], "EU · 德 / 法 / 西")
set_cell(t2.rows[2].cells[1], "德语 / 法语 / 西班牙语")
set_cell(t2.rows[2].cells[2], "Sie / vous / usted；首轮正式，熟悉后转非正式")
set_cell(t2.rows[2].cells[3], "功效宣称须有证据文件；医疗器械 MDR")

set_cell(t2.rows[3].cells[0], "US")
set_cell(t2.rows[3].cells[1], "英语")
set_cell(t2.rows[3].cells[2], "直接；道歉一次到位，重复道歉显廉价")
set_cell(t2.rows[3].cells[3], "膳食补充剂需 DSHEA 免责；FTC §5 误导性广告")

r = t2.rows[4]
set_cell(r.cells[0], "PH / KR / RU / MN")
set_cell(r.cells[1], "英语 / 韩语 / 俄语 / 蒙古语")
set_cell(r.cells[2], "条款待核实，以当地平台通用规则为准")
set_cell(r.cells[3], "共 20 条，全部标注「待核实」")

# TABLE 7 选型：知识检索一行
t7 = d.tables[7]
set_cell(t7.rows[3].cells[1], "知识库 26 条 → 关键词 + 同义词匹配（向量检索待接入）")

# TABLE 8 文件职责表：6 行 -> 11 行，按技术栈顺序重排
t8 = d.tables[8]
while len(t8.rows) < 12:
    add_row(t8)

file_rows = [
    ("app/compliance.py", "合规四级流水线、两类规则、自动改写与复检", "已跑通"),
    ("app/agent.py", "意图识别（要办 / 问规则分流）、订单工具、知识库检索、草稿生成、主链路", "已跑通"),
    ("app/llm.py", "模型客户端：JSON 结构化输出、重试与超时兜底，仅依赖标准库", "已跑通"),
    ("app/semantic.py", "语义兜底层：规则层放行后的二次判定，只加判不减判", "已跑通"),
    ("app/handoff.py", "人工会话状态：转接 / 交还 / 待办队列 / 安抚消息节流", "已跑通"),
    ("app/judge_log.py", "判定日志与统计：按市场、结果、语种、小时聚合", "已跑通"),
    ("app/rules_store.py", "规则热更新：校验、版本、回滚", "已跑通"),
    ("data/rules.json", "44 条合规规则（CN / EU / US 各 8 条，PH / KR / RU / MN 共 20 条标注待核实）", "已落地"),
    ("data/orders.json", "20 条 Mock 订单（覆盖 10 种状态）", "已落地"),
    ("data/kb.json", "知识库 26 条 FAQ 与政策条目，客服与系统共用同一份", "已落地"),
    ("web/app.py", "双角色界面：买家端对话 + 商家后台（接管 / 规则 / 日志 / 知识库）", "已上线"),
]
for i, row in enumerate(file_rows, start=1):
    for j, val in enumerate(row):
        set_cell(t8.rows[i].cells[j], val)

# TABLE 11 指标表：更新实测列
t11 = d.tables[11]
set_cell(t11.rows[2].cells[4], "2.0 – 3.5s")
set_cell(t11.rows[3].cells[4], "0.5 – 0.8s")
set_cell(t11.rows[4].cells[4], "约 2.8 次")

# TABLE 12 创新点：加 2 行
t12 = d.tables[12]
for name, mech, why in [
    ("人工闭环", "转人工不是终点：商家后台能接、能回、能交还，买家侧 4 秒轮询拉取",
     "多数演示到「已转人工」就结束了，闭环才叫可用"),
    ("语义兜底层", "规则放行后再做一次语义二次判定，只加判不减判",
     "补上规则天花板，又不破坏可解释性"),
]:
    r = add_row(t12)
    set_cell(r.cells[0], name)
    set_cell(r.cells[1], mech)
    set_cell(r.cells[2], why)

# TABLE 13 工期表：整体重排（用户 2026-10-31 指定 11/01-11/03 留给产品化打磨）
t13 = d.tables[13]
schedule = [
    ("10/22", "规则表 24 条、Mock 订单 20 条、端到端链路", "可跑通的 7 场景演示", "✅ 已完成"),
    ("10/23 – 10/25", "评测集 60 条 + 指标跑数", "指标表真实数字", "✅ 已完成（10-27）"),
    ("10/26 – 10/28", "Streamlit 界面 + trace 面板 + 商家后台雏形", "可演示界面（已上线公网）", "✅ 已完成"),
    ("10/29 – 10/31", "规则扩至 7 市场 44 条、语义兜底层、人工双向闭环、物流动画、三语切换、判定日志",
     "产品化版本", "✅ 已完成"),
    ("11/01 – 11/03", "产品化打磨：界面交互、异常态、联调与回归", "稳定发布版", "进行中"),
    ("11/04 – 11/06", "录制 6 分钟演示视频", "演示视频（MP4）", "待开始"),
    ("11/07 – 11/08", "答辩 PPT + 作品计划书终稿", "pptx / docx", "待开始"),
    ("11/09 – 11/10", "缓冲、报名提交", "提交完成", "待开始"),
]
for i, row in enumerate(schedule, start=1):
    for j, val in enumerate(row):
        set_cell(t13.rows[i].cells[j], val)

# 工期表列宽：「任务」列内容最长，重新分配（日期 3.2 / 任务 7.3 / 交付物 3.0 / 状态 2.6）
col_widths = [Cm(3.2), Cm(7.3), Cm(3.0), Cm(2.6)]
t13.autofit = False
for i, w in enumerate(col_widths):
    t13.columns[i].width = w
for row in t13.rows:
    for i, w in enumerate(col_widths):
        row.cells[i].width = w

# TABLE 17 访问表：账号信息
t17 = d.tables[17]
set_cell(t17.rows[2].cells[0], "买家端账号")
set_cell(t17.rows[2].cells[1], "buyer / niao2026（体验对客对话、转人工）")
set_cell(t17.rows[3].cells[0], "商家后台账号")
set_cell(t17.rows[3].cells[1], "admin / niao2026（体验接管、规则编辑、判定日志）")
set_cell(t17.rows[4].cells[1], "5–8 分钟：先在买家端问一单物流，再切商家后台接管一次，能看完整个闭环")

# ---------------------------------------------------------------- 插入新内容
# 概述：加「商家后台」这一形态
insert_before(P[11], "商家后台（商家侧）：会话接管、规则编辑、判定日志、知识库维护，运营在界面上点，不需要改代码。",
              "List Bullet")

# 4.2 物流动画
insert_before(P[30],
              "界面侧把物流节点画成一条逐步推进的路线（发货仓 → 出境 → 目的国分拣 → 派送），"
              "当前节点脉动高亮，买家一眼能看出卡在哪个环节，而不是只读一行状态文字。")

# 4.3 之后：问规则 vs 要办 的分流
insert_before(P[36],
              "这里有一条明确的分流规则：「问规则」交给 AI，「要办事」交给人工。买家问退货流程、保修期限、"
              "政策条款 → AI 直接答；买家说「我要退」「我要换」「这个坏了要修」「赔我钱」→ 属于事务动作，"
              "一律直接转人工，不再追问订单号、不生成任何承诺。这条线是人工流量的主要来源，"
              "也是「不该由 AI 拍板的事绝不由 AI 拍板」的落地。")

# 4.6 商家后台（插在「五、技术架构」之前）
anchor = P[62]
insert_before(anchor, "4.6 商家后台（双角色）", "Heading 2")
insert_before(anchor,
              "同一套代码两个角色：买家端只看到对话；商家登录后台，看到的是一张能干活的工作台。"
              "这套后台不是演示壳——运营真正需要的四个动作都能在界面上完成，不需要改代码或改文件。")
insert_before(anchor,
              "会话列表：按「AI / 待人工 / 人工中」分组，未读角标，点开即见完整对话与每条回复的判定依据。",
              "List Bullet")
insert_before(anchor,
              "人工接管：客服直接回复，回复落库并推给买家；处理完点「结束会话（交还 AI）」。",
              "List Bullet")
insert_before(anchor,
              "规则管理：可视化编辑、导入导出、即时生效，带版本记录与一键回滚。",
              "List Bullet")
insert_before(anchor,
              "判定日志：每条回复的意图、判定结果、命中条款、是否改写、耗时，可按市场 / 结果 / 语种 / 时段筛选。",
              "List Bullet")
insert_before(anchor,
              "知识库：FAQ 与政策条目的增删改查，客服与 AI 读的是同一份。",
              "List Bullet")

# 场景六：商家后台接管（插在「八、效果验证指标」之前）
anchor = P[94]
insert_before(anchor, "场景六 · 商家后台接管（产品化证据）", "Heading 2")
insert_before(anchor,
              "买家：I want to return this item, it arrived defective.")
insert_before(anchor,
              "判定：属于「要办」类诉求（退货）→ 直接转人工，不追问订单号、不生成承诺。")
insert_before(anchor, "买家看到：已为您转接人工客服，请稍候。（不承诺时效与结果）")
insert_before(anchor,
              "商家后台：会话列表出现待接管会话 → 客服点开看到完整对话与判定链 → 回复 → "
              "买家页 4 秒内拉到该回复 → 客服点「结束会话（交还 AI）」。")
insert_before(anchor,
              "这一段的价值：证明它不是只有聊天窗口的 demo，商家真的能拿它干活。")

# ---------------------------------------------------------------- 保存
if errors:
    print("\n".join(errors))
    sys.exit(1)

d.save(DST)
print("saved:", DST)
print("paragraphs:", len(docx.Document(DST).paragraphs),
      " tables:", len(docx.Document(DST).tables))
