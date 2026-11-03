# -*- coding: utf-8 -*-
"""跑 probe_qp_app.py 的四种写法，看哪种能把 l= 写进地址栏。"""
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
    opt = pg.locator('[role="option"]').filter(has_text=value)
    opt.last.click(timeout=5000)
    time.sleep(4)


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    for tag in ["A", "B", "C", "D"]:
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.goto(BASE + "?mode=" + tag, wait_until="domcontentloaded", timeout=60000)
        time.sleep(7)
        print(f"[{tag}] 初始值={sel_value(pg)!r}")
        pick(pg, "th")
        print(f"[{tag}] 切完 URL = {pg.url}")
        print(f"     下拉框现在 = {sel_value(pg)!r}")
        pg.reload(wait_until="domcontentloaded")
        time.sleep(7)
        print(f"     刷新后下拉框 = {sel_value(pg)!r}  URL = {pg.url}")
        pg.close()
    b.close()
