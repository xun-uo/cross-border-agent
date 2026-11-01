# -*- coding: utf-8 -*-
"""生成《明天测试清单》Word 文档。"""
import io
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUT = Path(r"D:\1\Desktop\跨境智服Agent-明天测试清单.docx")

d = Document()

# 中文字体
st = d.styles["Normal"]
st.font.name = "Microsoft YaHei"
st.font.size = Pt(10.5)
st._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
for lvl in ("Heading 1", "Heading 2", "Heading 3"):
    s = d.styles[lvl]
    s.font.name = "Microsoft YaHei"
    s._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")


def h(text, level=1):
    d.add_heading(text, level=level)


def p(text="", bold=False):
    par = d.add_paragraph()
    run = par.add_run(text)
    run.bold = bold
    return par


def bullet(text):
    d.add_paragraph(text, style="List Bullet")


def table(rows, widths=None):
    t = d.add_table(rows=1, cols=len(rows[0]))
    t.style = "Light Grid Accent 1"
    for i, c in enumerate(rows[0]):
        cell = t.rows[0].cells[i]
        cell.text = c
        cell.paragraphs[0].runs[0].bold = True
    for r in rows[1:]:
        cells = t.add_row().cells
        for i, c in enumerate(r):
            cells[i].text = str(c)
    return t


h("跨境智服 Agent · 明天测试清单", 0)
p("2026-11-01 版　·　代码 #117　·　PPT v13　·　计划书 v8")
d.add_paragraph()

# ---------------------------------------------------------------- 访问
h("一、访问方式", 1)

p("两种环境，各有用处：线上用来验真实部署，本地用来快速反复试。", True)
d.add_paragraph()

h("线上（推荐先用这个）", 2)
table([
    ["项", "内容"],
    ["地址", "https://cross-border-agent.streamlit.app"],
    ["注意", "免费实例闲置会休眠，首次打开等 30–60 秒，属正常"],
    ["优点", "就是评委看到的样子，含部署环境差异"],
    ["缺点", "改代码不会实时生效，要等重新部署"],
])

d.add_paragraph()
h("本地（改了东西想马上验时用）", 2)
p("先在这个目录开一个 PowerShell，粘下面这行：")
p("cd D:\\跨境智服; .venv\\Scripts\\python.exe -m streamlit run web\\app.py "
  "--server.port 8502 --server.headless=true --server.fileWatcherType=none", True)
p("然后浏览器打开：http://localhost:8502")
p("这个实例不会自动重载，改完代码要按 Ctrl+C 停掉重开。", bold=True)

d.add_paragraph()
h("账号", 2)
table([
    ["角色", "账号", "说明"],
    ["买家", "订单号 ORDER20261021001 + 手机尾号 0001", "主推方式，登录后自动绑定该订单"],
    ["买家（游客）", "buyer / niao2026", "不绑订单，问物流时会追问订单号"],
    ["商家（主）", "admin / niao2026", "可体验接管、规则编辑、判定日志"],
    ["商家（备）", "judge / xinghe2026", "用来测「归属控制」的第二个人"],
])

d.add_paragraph()
h("可用的订单号（尾号 = 订单号后四位）", 2)
table([
    ["市场", "订单号", "尾号", "状态"],
    ["美国", "ORDER20261021001", "0001", "在途"],
    ["欧盟", "ORDER20261021003", "0003", "异常"],
    ["菲律宾", "ORDER20261021022", "0022", "清关滞留"],
    ["韩国", "ORDER20261021023", "0023", "在途"],
    ["俄罗斯", "ORDER20261021026", "0026", "退货处理中"],
    ["蒙古", "ORDER20261021028", "0028", "派送异常"],
    ["中国", "ORDER20261021030", "0030", "已退款"],
    ["英国", "ORDER20261021032", "0032", "清关滞留"],
    ["日本", "ORDER20261021034", "0034", "清关滞留"],
])

# ---------------------------------------------------------------- 测试点
d.add_page_break()
h("二、推荐测试顺序（按最容易翻车排）", 1)
p("不要从首页乱点。按下面顺序走，前面几条是今天刚改过的地方，最可能出问题。")

h("① 规则编辑是否真生效（今天刚修的，优先测）", 2)
p("步骤：")
bullet("商家登录 admin → 规则库 tab")
bullet("看顶部三个数字：规则总数 59 / 已核对 39 / 示例待核 20")
bullet("在下方表格里找 ID 为 KR-SUP-8-1 的那行，把 patterns 里的「항암」改成「__test__」")
bullet("点「保存修改」")
bullet("换买家登录 ORDER20261021023（韩国单，尾号 0023），发一句：이 제품은 항암 효과가 있습니다")
p("预期：改之前这句应被拦截；改完规则后再发同样的话，应改成放行。")
p("失败长什么样：改完规则，判定结果一点没变——那说明「后台改规则即时生效」这条又断了。", bold=True)
p("测完记得把规则改回去，或点「版本回滚」恢复。")

h("② 语言全链路", 2)
p("步骤（买家端）：")
bullet("登录后先问一句「我的订单到哪了」，等回复出来")
bullet("右上角语言切到 ไทย")
bullet("观察：历史里 AI 那段回复是否变成泰文（买家自己的话应该保持中文不变）")
bullet("按 F5 刷新，看语言是否还是泰语")
bullet("切回中文，再发一句新问题，看是不是用中文回答")
p("预期：气泡跟着变、刷新后语言保持、新消息用当前语言。")
p("失败长什么样：切了语言历史还是中文，或者刷新后变回中文。", bold=True)

h("③ 转人工 + 归属控制", 2)
p("步骤：")
bullet("买家登录，发「我要退货」")
bullet("看是否转人工、页头是否显示等待状态")
bullet("商家 admin 登录 → 待处理会话，找到这一单，点开")
bullet("回复一句「已收到，稍后处理」")
bullet("买家页面别动，等 4–6 秒，看是否自动出现这句回复")
bullet("另开一个浏览器，用 judge / xinghe2026 登录，看这一个会话在不在它的列表里")
p("预期：admin 回复后买家自动收到；judge 看不到这个会话（已被 admin 接管）。")
p("失败长什么样：两个商家都能看到同一单（归属失效），或买家一直收不到回复。", bold=True)

h("④ 人工回复也过合规（核心卖点）", 2)
p("步骤：商家在接管中的会话里，回复「这个产品绝对能治好你的病，保证有效」")
p("预期：被拦下，提示命中条款，不让发出去。")
p("失败长什么样：这句话直接发给买家了——这是最尴尬的一种，等于说「合规」只管 AI 不管人。", bold=True)

h("⑤ 刷新与多标签", 2)
bullet("转人工状态下刷新买家页面：会话和等待状态是否还在")
bullet("同一个买家开两个标签页，两边看到的对话是否一致")
bullet("浏览器后退按钮按几下，看会不会进到奇怪的状态")

h("⑥ 异常输入", 2)
bullet("粘 5000 字的超长文本发出去")
bullet("发纯 emoji 和纯符号")
bullet("上传一张 5MB 的图片（限 10MB）")
bullet("把 .txt 改成 .png 再上传，看怎么处理")

h("⑦ 数据边界", 2)
bullet("查不存在的订单 ORDER99999999999，看追问话术")
bullet("登录时手机尾号输错（如 9999），看错误提示")
bullet("问清关滞留的单（ORDER20261021022 / 0032 / 0034），看话术是否说明卡在哪")
bullet("问已退款的单（ORDER20261021030），看怎么说")

h("⑧ 并发与额度", 2)
bullet("两个浏览器同时各问一句，看会不会串号")
bullet("同一句连续快速发 5 次，看有没有重复回复或丢消息")

# ---------------------------------------------------------------- 已知
d.add_page_break()
h("三、今天已知没修的问题（别当新 bug 报）", 1)
table([
    ["现象", "原因", "严重度"],
    ["商家端登录瞬间约有 1 秒两层叠加", "Streamlit 重跑的过渡帧，刷新不复现", "低"],
    ["商家端消息区底部有一片空白", "滚动区高度写死 560px，窗口更高就留白", "低"],
    ["切到深色模式后物流图配色不协调", "只固定了浅色主题，深色没做第二套配色", "低"],
    ["实例重启后会话记录清空", "会话存在内存里，没有落数据库", "中，但要重启才会遇到"],
    ["20 条规则条款标注「待核实」", "菲律宾/韩国/俄罗斯/蒙古的官方原文还没拿到", "中，材料里已如实标注"],
])

h("四、怎么记结果", 1)
p("每条只记三样，别写分析：")
bullet("现象：你看到什么（一句话）")
bullet("截图：全屏，带地址栏")
bullet("复现：刷新还能不能再出现（能 / 不能）")
p("原因我来定位，你不用猜。")

d.add_paragraph()
p("补充：开测前先确认版本号。打开首页，登录框下方那行小字末尾就写着 build 号，"
  "应该是 #117；不是的话说明线上还没部署完，等几分钟再刷新。", bold=True)

d.save(str(OUT))
print("saved:", OUT)


chk = Document(str(OUT))
print("段落数:", len(chk.paragraphs), "| 表格数:", len(chk.tables))
