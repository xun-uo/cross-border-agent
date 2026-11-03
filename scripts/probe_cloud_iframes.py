# -*- coding: utf-8 -*-
"""线上：iframe 清单与 srcdoc 情况。"""
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
    n = pg.locator("iframe").count()
    print("iframe elements:", n)
    for i in range(n):
        el = pg.locator("iframe").nth(i)
        print("  ", i, "src=", el.get_attribute("src"), "| id=", el.get_attribute("id"),
              "| srcdoc_len=", len(el.get_attribute("srcdoc") or ""),
              "| title=", el.get_attribute("title"))
    for i, f in enumerate(pg.frames):
        print(f"frame{i} url={f.url!r}")
        try:
            c = f.content()
            print(f"   content len={len(c)} has订单号={'订单号' in c}")
        except Exception as e:
            print("   content ERR", e)
    b.close()
