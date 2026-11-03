# -*- coding: utf-8 -*-
"""买家端常规冒烟：登录 → 问一句 → 有没有 AI 回复 → 切泰语 → 历史气泡有没有跟着翻。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"


def has_thai(s):
    return any("\u0e00" <= c <= "\u0e7f" for c in s)


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(9)
    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    for _ in range(15):
        time.sleep(3)
        if pg.locator('[data-testid="stChatMessage"]').count() >= 3:
            break
    n = pg.locator('[data-testid="stChatMessage"]').count()
    print("气泡数:", n)
    bodies = [x.inner_text().replace("\n", " ")[:70] for x in pg.locator('[data-testid="stChatMessage"]').all()]
    for x in bodies:
        print("  ", x)
    pg.screenshot(path="D:/跨境智服/out/smoke_buyer.png")

    pg.locator('[data-testid="stSelectbox"]').first.click()
    time.sleep(1.5)
    pg.locator('[role="option"]').filter(has_text="ไทย").last.click()
    time.sleep(14)
    txt = pg.locator("body").inner_text()
    print("界面泰语:", has_thai(txt))
    print("URL:", pg.evaluate("() => location.search"))
    after = [x.inner_text().replace("\n", " ")[:70] for x in pg.locator('[data-testid="stChatMessage"]').all()]
    for x in after:
        print("  切后:", x)
    pg.reload(wait_until="domcontentloaded")
    time.sleep(12)
    print("刷新后泰语:", has_thai(pg.locator("body").inner_text()))
    b.close()
