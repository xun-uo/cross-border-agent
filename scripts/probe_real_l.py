# -*- coding: utf-8 -*-
"""在真实 app 上复现 #38：切语言后地址栏 l= 到底有没有写、写了之后有没有被改回去。"""
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
    print("登录后 URL:", pg.url)

    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    for _ in range(12):
        time.sleep(3)
        if pg.locator('[data-testid="stChatMessage"]').count() >= 3:
            break
    print("气泡数:", pg.locator('[data-testid="stChatMessage"]').count())
    print("切语言前 URL:", pg.evaluate("() => location.search"))

    pg.locator('[data-testid="stSelectbox"]').first.click(timeout=8000)
    time.sleep(1.5)
    opt = pg.locator('[role="option"]').filter(has_text="ไทย")
    print("泰语选项:", opt.count())
    opt.last.click(timeout=5000)

    seen = []
    for i in range(40):
        time.sleep(0.5)
        href = pg.evaluate("() => location.search")
        if not seen or seen[-1][1] != href:
            seen.append((round((i + 1) * 0.5, 1), href))
    print("--- 地址栏变化轨迹 ---")
    for t, h in seen:
        print(f"  {t:>5}s  {h}")
    print("界面是泰语吗:", has_thai(pg.locator("body").inner_text()))
    print("此时 URL:", pg.evaluate("() => location.search"))

    pg.reload(wait_until="domcontentloaded")
    time.sleep(10)
    print("刷新后 URL:", pg.evaluate("() => location.search"))
    print("刷新后界面是泰语吗:", has_thai(pg.locator("body").inner_text()))
    b.close()
