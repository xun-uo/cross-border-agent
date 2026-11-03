# -*- coding: utf-8 -*-
"""验 #40：物流图下面的「现在到哪了」+ 点开放大弹窗。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(10)
    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    for _ in range(20):
        time.sleep(3)
        if pg.get_by_text("正在处理").count() == 0 and pg.locator('[data-testid="stChatMessage"]').count() >= 2:
            break
    time.sleep(3)
    print("气泡数:", pg.locator('[data-testid="stChatMessage"]').count())
    for x in pg.locator('[data-testid="stChatMessage"]').all():
        print("  气泡:", x.inner_text().replace("\n", " ")[:160])
    print("有『现在到哪了』:", pg.get_by_text("现在到哪了").count())
    print("放大按钮:", pg.get_by_role("button", name="点开放大").count())
    print("轨迹明细:", pg.get_by_text("轨迹明细").count())
    pg.screenshot(path="D:/跨境智服/out/route40_inline.png", full_page=False)

    btn = pg.get_by_role("button", name="点开放大")
    if btn.count():
        btn.first.click()
        time.sleep(4)
        dlg = pg.locator('[role="dialog"]')
        print("弹窗数:", dlg.count())
        if dlg.count():
            print("弹窗文字片段:", dlg.first.inner_text()[:200].replace("\n", " | "))
            pg.screenshot(path="D:/跨境智服/out/route40_dialog.png")
    b.close()
