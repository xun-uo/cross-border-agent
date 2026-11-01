# -*- coding: utf-8 -*-
"""验语言全链路：历史重译 / 刷新保持 / 处理过程面板 / 物流图悬停提示。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"
THAI = re.compile(r"[\u0e00-\u0e7f]")


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


def ph(pg):
    try:
        return pg.locator('[data-testid="stChatInput"] textarea').first.get_attribute("placeholder")
    except Exception:
        return None


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 1100})
    pg = ctx.new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(10)

    # 先在中文下发一条，攒出历史
    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    time.sleep(16)
    t0 = body(pg)
    print("[zh] 气泡里有中文回复 =", "运输" in t0 or "在途" in t0 or "订单" in t0)
    print("[zh] 圆点 title 数量 =", pg.locator("circle > title").count())

    # 切泰语
    pg.locator('[data-testid="stSelectbox"]').first.click(timeout=5000)
    time.sleep(1)
    pg.get_by_text("ไทย", exact=True).last.click(timeout=3000)
    time.sleep(16)

    t1 = body(pg)
    thai_lines = [ln for ln in t1.splitlines() if THAI.search(ln) and len(ln) > 12]
    print("[th] 泰文长句条数 =", len(thai_lines))
    if thai_lines:
        print("     示例:", thai_lines[0][:90])
    print("[th] 仍残留中文气泡 =", "运输途中" in t1 or "承运商为" in t1)
    print("[th] 圆点 title 数量 =", pg.locator("circle > title").count())
    if pg.locator("circle > title").count():
        print("     第一条 title:", pg.eval_on_selector("circle > title", "e => e.textContent")[:80])

    # 刷新看语言是否保持
    pg.reload(wait_until="domcontentloaded")
    time.sleep(14)
    print("[reload] placeholder =", ph(pg))
    print("[reload] url =", pg.url[:220])
    pg.screenshot(path=r"D:\跨境智服\out\scan_lang2.png", full_page=False)
    b.close()
