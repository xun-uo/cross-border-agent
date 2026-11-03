# -*- coding: utf-8 -*-
"""线上页面结构：内容在不在 iframe 里，登录输入框怎么定位。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto("https://cross-border-agent.streamlit.app", wait_until="domcontentloaded", timeout=120000)
    time.sleep(20)
    print("frames:", [(f.name, f.url[:80]) for f in pg.frames])
    print("body len:", len(pg.locator("body").inner_text()))
    print("inputs:", pg.locator("input").count())
    for i in range(min(pg.locator("input").count(), 6)):
        el = pg.locator("input").nth(i)
        print("  input", i, el.get_attribute("aria-label"), el.get_attribute("placeholder"))
    print("stTextInput:", pg.locator('[data-testid="stTextInput"]').count())
    print("app root:", pg.locator('[data-testid="stApp"]').count(),
          "| stAppViewContainer:", pg.locator('[data-testid="stAppViewContainer"]').count())
    b.close()
