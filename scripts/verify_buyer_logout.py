# -*- coding: utf-8 -*-
"""验买家端退出登录：页头有按钮、点了能回登录页、语言跟着变。"""
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


def login_buyer(pg):
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 1000})
    pg = ctx.new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    login_buyer(pg)
    time.sleep(10)

    t = body(pg)
    print("登录成功:", "订单号" not in t)
    print("页头含『退出登录』:", "退出登录" in t)
    btn = pg.locator("a.logout-inline")
    print("退出链接数量:", btn.count())
    if btn.count():
        box = btn.first.bounding_box()
        print("退出按钮位置:", box)
    pg.screenshot(path=r"D:\跨境智服\out\buyer_logout_btn.png", full_page=False)

    # 点退出
    if btn.count():
        btn.first.click()
        time.sleep(6)
        t2 = body(pg)
        print("点完回登录页:", "订单号" in t2 and "手机号后四位" in t2)
        print("退出后 URL:", pg.url[:120])

    # 英文界面下按钮文案
    pg.goto(URL, wait_until="domcontentloaded", timeout=60000)
    time.sleep(7)
    try:
        pg.locator('[data-testid="stSelectbox"]').first.click(timeout=5000)
        time.sleep(1)
        pg.get_by_text("English", exact=True).last.click(timeout=3000)
        time.sleep(4)
        login_buyer(pg)
        time.sleep(9)
        t3 = body(pg)
        print("英文界面含『Sign out』:", "Sign out" in t3)
    except Exception as e:
        print("英文测试跳过:", e)
    b.close()
