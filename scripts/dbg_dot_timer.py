# -*- coding: utf-8 -*-
"""看红点那条 fragment 的 run_every 到底有没有在跑（临时 DOTDBG 文案）。"""
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
    pg.locator('[role="tab"]').nth(1).click()
    time.sleep(3)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    for _ in range(20):
        time.sleep(2)
        if pg.locator('[role="tablist"]').count():
            break
    for i in range(5):
        time.sleep(4)
        dbg = [x for x in pg.locator("body").inner_text().split("\n") if "DOTDBG" in x]
        print(f"t={4*(i+1)}s", dbg[:1])
    b.close()
