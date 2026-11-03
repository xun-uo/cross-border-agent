# -*- coding: utf-8 -*-
"""细看：切完语言后地址栏到底什么时候变，以及「URL 里本来就有 l=zh」时还变不变。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "http://localhost:8511/"


def sel_value(pg):
    try:
        return pg.locator('[data-testid="stSelectbox"] input[role="combobox"]').first.input_value()
    except Exception:
        return "?"


def pick(pg, value):
    pg.locator('[data-testid="stSelectbox"]').first.click(timeout=8000)
    time.sleep(1.2)
    pg.locator('[role="option"]').filter(has_text=value).last.click(timeout=5000)


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    for tag, start in [("A", "?mode=A"), ("A", "?mode=A&l=zh"), ("B", "?mode=B&l=zh"), ("C", "?mode=C&l=zh")]:
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.goto(BASE + start, wait_until="domcontentloaded", timeout=60000)
        time.sleep(7)
        pick(pg, "th")
        seen = []
        for i in range(20):
            time.sleep(0.5)
            href = pg.evaluate("() => location.search")
            if not seen or seen[-1][1] != href:
                seen.append((round((i + 1) * 0.5, 1), href))
        print(f"[mode={tag} start={start}] 值={sel_value(pg)!r}")
        for t, h in seen:
            print(f"    {t:>5}s  {h}")
        pg.close()
    b.close()
