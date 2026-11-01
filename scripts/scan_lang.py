# -*- coding: utf-8 -*-
"""验：切语言后，新发的消息 AI 用什么语言回。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


def bubbles(pg):
    out = []
    for el in pg.query_selector_all('[data-testid="stChatMessage"]'):
        try:
            out.append(el.inner_text())
        except Exception:
            pass
    return out


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

    # 切泰语
    try:
        pg.locator('[data-testid="stSelectbox"]').first.click(timeout=5000)
        time.sleep(1)
        pg.get_by_text("ไทย", exact=True).last.click(timeout=3000)
        print("[lang] switched to th")
    except Exception as e:
        print("[lang] switch failed:", e)
    time.sleep(6)

    # 发消息
    box = pg.locator('[data-testid="stChatInput"] textarea').first
    try:
        box.fill("我的订单到哪了")
        box.press("Enter")
        print("[send] ok")
    except Exception as e:
        print("[send] fail:", e)

    time.sleep(18)
    for i, t in enumerate(bubbles(pg)):
        print("--- bubble %d ---" % i)
        print(t[:300])
    pg.screenshot(path=r"D:\跨境智服\out\scan_lang_newmsg.png", full_page=False)
    b.close()
