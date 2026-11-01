# -*- coding: utf-8 -*-
"""验两件事：① 切语言后刷新，语言还在不在；② 转人工后刷新，会话还在不在。"""
import io
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


def ph(pg):
    try:
        return pg.locator('[data-testid="stChatInput"] textarea').first.get_attribute("placeholder")
    except Exception:
        return None


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

    print("[start] placeholder =", ph(pg))
    url0 = pg.url
    print("[start] url =", url0[:160])

    # 切泰语
    try:
        pg.locator('[data-testid="stSelectbox"]').first.click(timeout=5000)
        time.sleep(1)
        pg.get_by_text("ไทย", exact=True).last.click(timeout=3000)
        time.sleep(6)
        print("[after-switch] placeholder =", ph(pg))
    except Exception as e:
        print("[switch] FAIL", e)

    # 刷新
    pg.reload(wait_until="domcontentloaded")
    time.sleep(12)
    print("[after-reload] placeholder =", ph(pg))
    print("[after-reload] url =", pg.url[:160])
    print("[after-reload] logged_in =", "订单号" not in body(pg))

    # 转人工
    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我要退货，帮我转人工处理")
    box.press("Enter")
    time.sleep(20)
    print("[handoff] url =", pg.url[:200])
    t = body(pg)
    for kw in ("人工", "等待", "转接"):
        print("[handoff] body has %r: %s" % (kw, kw in t))

    # 刷新看会话是否还在
    pg.reload(wait_until="domcontentloaded")
    time.sleep(14)
    t2 = body(pg)
    print("[handoff-reload] logged_in =", "订单号" not in t2)
    print("[handoff-reload] still has my msg =", "我要退货" in t2)
    print("[handoff-reload] shows waiting =", ("人工" in t2))
    print("[handoff-reload] url =", pg.url[:200])
    pg.screenshot(path=r"D:\跨境智服\out\scan_handoff_reload.png", full_page=False)
    b.close()
