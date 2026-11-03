# -*- coding: utf-8 -*-
"""线上：第二个 frame 里才是 app。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto("https://cross-border-agent.streamlit.app", wait_until="domcontentloaded", timeout=120000)
    time.sleep(22)
    print("frames:", len(pg.frames))
    for i, f in enumerate(pg.frames):
        try:
            n = f.locator("body").count()
            t = f.locator("body").inner_text()[:120] if n else ""
            print(f"  frame{i}: url={f.url[:60]!r} bodyText={t!r}")
        except Exception as e:
            print(f"  frame{i}: ERR {e}")
    f = pg.frames[-1]
    print("last frame inputs:", f.locator("input").count())
    for i in range(min(f.locator("input").count(), 8)):
        el = f.locator("input").nth(i)
        print("   ", i, "aria=", el.get_attribute("aria-label"), "ph=", el.get_attribute("placeholder"))
    b.close()
