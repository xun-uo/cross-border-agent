# -*- coding: utf-8 -*-
"""判断退出链接点击为什么不生效：JS 跳转 vs 点击，各测一遍。"""
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


def login(pg):
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)

    # A：JS 强制跳转
    pg = b.new_page(viewport={"width": 1440, "height": 1000})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    login(pg)
    time.sleep(9)
    print("[A] 登录后 URL:", pg.url[:90])
    pg.evaluate("() => { window.location.href = '?logout=1'; }")
    time.sleep(9)
    print("[A] JS 跳转后 URL:", pg.url[:90], "| 回登录页:", "手机号后四位" in body(pg))

    # B：真实点击，并等导航事件
    pg2 = b.new_page(viewport={"width": 1440, "height": 1000})
    pg2.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    login(pg2)
    time.sleep(9)
    print("[B] 登录后 URL:", pg2.url[:90])
    try:
        with pg2.expect_navigation(timeout=15000):
            pg2.locator("a.logout-inline").first.click()
        print("[B] 点击触发了导航")
    except Exception as e:
        print("[B] 点击没有触发导航:", type(e).__name__)
    time.sleep(9)
    print("[B] 点击后 URL:", pg2.url[:90], "| 回登录页:", "手机号后四位" in body(pg2))

    # C：链接的真实 href 是什么
    href = pg2.locator("a.logout-inline").first.get_attribute("href")
    print("[C] 链接 href =", repr(href))
    b.close()
