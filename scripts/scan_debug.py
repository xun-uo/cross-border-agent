# -*- coding: utf-8 -*-
"""验 ?debug=1 下处理过程面板是否跟随语言。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502/?debug=1"


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 1100})
    pg = ctx.new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(10)

    # 打开「显示处理过程」开关（?debug=1 只让开关出现，默认是关的）
    try:
        pg.get_by_text("显示处理过程").first.click(timeout=6000)
        print("[toggle] on")
    except Exception as e:
        print("[toggle] fail", e)
    time.sleep(5)

    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    time.sleep(18)
    t0 = body(pg)
    print("[zh] 处理过程 =", "处理过程" in t0, "| 判定 =", "判定：" in t0)

    try:
        pg.locator('[data-testid="stSelectbox"]').first.click(timeout=5000)
        time.sleep(1)
        pg.get_by_text("English", exact=True).last.click(timeout=3000)
        time.sleep(12)
    except Exception as e:
        print("[switch] fail", e)

    t1 = body(pg)
    print("[en] Pipeline =", "Pipeline" in t1)
    print("[en] Verdict  =", "Verdict:" in t1)
    print("[en] Total    =", "Total" in t1)
    print("[en] 残留中文面板 =", "处理过程" in t1 or "判定：" in t1)
    pg.screenshot(path=r"D:\跨境智服\out\scan_debug_en.png", full_page=False)
    b.close()
