# -*- coding: utf-8 -*-
"""诊断：切语言到底有没有生效、AI 有没有回。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(9)
    print("登录后 URL:", pg.url)

    # 发一句，等久一点
    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    for i in range(12):
        time.sleep(3)
        n = pg.locator('[data-testid="stChatMessage"]').count()
        if n >= 3:
            print("AI 已回复，气泡数:", n, "，用了", (i + 1) * 3, "秒")
            break
    else:
        print("30 秒内没等到 AI 回复，气泡数:", pg.locator('[data-testid="stChatMessage"]').count())
        print("body 片段:", body(pg)[:200].replace("\n", " | "))

    # 切语言：先确认有几个 selectbox
    boxes = pg.locator('[data-testid="stSelectbox"]')
    print("selectbox 数量:", boxes.count())
    for i in range(boxes.count()):
        try:
            print("  第%d个 box:" % i, boxes.nth(i).bounding_box())
        except Exception:
            pass

    boxes.first.click(timeout=8000)
    time.sleep(1.5)
    opts = pg.get_by_text("ไทย", exact=True)
    print("泰国选项数:", opts.count())
    if opts.count():
        opts.last.click(timeout=5000)
    time.sleep(15)
    print("切完 URL:", pg.url)
    print("body 含泰文:", any("\u0e00" <= c <= "\u0e7f" for c in body(pg)))
    for x in pg.locator('[data-testid="stChatMessage"]').all():
        print("   气泡:", x.inner_text().replace("\n", " ")[:80])

    b.close()
