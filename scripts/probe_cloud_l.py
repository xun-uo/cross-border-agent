# -*- coding: utf-8 -*-
"""线上验证 #38：切泰语后地址栏 l= 有没有变、刷新后语言还在不在。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "https://cross-border-agent.streamlit.app"


def has_thai(s):
    return any("\u0e00" <= c <= "\u0e7f" for c in s)


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=120000)
    time.sleep(12)
    # 冷启动可能要点一次唤醒按钮
    wake = pg.get_by_role("button", name="Yes, get this app back up!")
    if wake.count():
        print("冷启动，点唤醒")
        wake.first.click()
        time.sleep(25)
    print("页面标题:", pg.title())
    print("build 行:", [x for x in pg.locator("body").inner_text().split("\n") if "build" in x][:2])
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(12)
    print("登录后 URL:", pg.evaluate("() => location.search"))

    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    for _ in range(15):
        time.sleep(3)
        if pg.locator('[data-testid="stChatMessage"]').count() >= 3:
            break
    print("气泡数:", pg.locator('[data-testid="stChatMessage"]').count())

    pg.locator('[data-testid="stSelectbox"]').first.click(timeout=10000)
    time.sleep(2)
    opt = pg.locator('[role="option"]').filter(has_text="ไทย")
    print("泰语选项:", opt.count())
    opt.last.click(timeout=8000)

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
    pg.screenshot(path="D:/跨境智服/out/cloud_lang_after.png")

    pg.reload(wait_until="domcontentloaded")
    time.sleep(14)
    print("刷新后 URL:", pg.evaluate("() => location.search"))
    print("刷新后界面是泰语吗:", has_thai(pg.locator("body").inner_text()))
    b.close()
