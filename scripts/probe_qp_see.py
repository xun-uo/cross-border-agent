# -*- coding: utf-8 -*-
"""看 selectbox 的 DOM 结构，找到正确的点击/选值方式。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.goto("http://localhost:8511/?mode=A", wait_until="domcontentloaded", timeout=60000)
    time.sleep(8)
    html = pg.locator('[data-testid="stSelectbox"]').first.evaluate("e => e.outerHTML")
    print(html[:1200])
    pg.locator('[data-testid="stSelectbox"]').first.click()
    time.sleep(1.5)
    print("--after click--")
    print("listbox:", pg.locator('[role="listbox"]').count(),
          "| option:", pg.locator('[role="option"]').count())
    print(pg.locator('[role="option"]').all_inner_texts()[:8] if pg.locator('[role="option"]').count() else "")
    b.close()
