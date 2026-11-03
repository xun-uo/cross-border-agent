# -*- coding: utf-8 -*-
"""线上刷新丢语言：刷新后到底显示什么语言、URL 是什么。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CLOUD = "https://cross-border-agent.streamlit.app"


def app_frame(pg, wait=90):
    t0 = time.time()
    while time.time() - t0 < wait:
        for f in pg.frames:
            if f is pg.main_frame:
                continue
            try:
                if f.locator('[data-testid="stApp"]').count():
                    return f
            except Exception:
                pass
        time.sleep(2)
    return None


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(CLOUD, wait_until="domcontentloaded", timeout=120000)
    f = app_frame(pg)
    f.get_by_label("订单号").fill("ORDER20261021001")
    f.get_by_label("手机号后四位").fill("0001")
    f.get_by_label("手机号后四位").press("Enter")
    time.sleep(14)
    f = app_frame(pg)
    f.locator('[data-testid="stSelectbox"]').first.click(timeout=10000)
    time.sleep(2)
    f.locator('[role="option"]').filter(has_text="ไทย").last.click(timeout=8000)
    time.sleep(8)
    print("切完 location.search:", pg.evaluate("() => location.search"))
    f = app_frame(pg)
    print("切完 body 开头:", repr(f.locator("body").inner_text()[:200]))

    pg.reload(wait_until="domcontentloaded")
    time.sleep(25)
    f = app_frame(pg)
    print("刷新后 location.search:", pg.evaluate("() => location.search"))
    body = f.locator("body").inner_text()
    print("刷新后 body 开头:", repr(body[:300]))
    pg.screenshot(path="D:/跨境智服/out/cloud_reload_lang.png")
    b.close()
