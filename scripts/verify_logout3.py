# -*- coding: utf-8 -*-
"""验买家/商家两端的退出按钮都能真正退出。"""
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


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)

    # 买家
    pg = b.new_page(viewport={"width": 1440, "height": 1000})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(10)
    print("[买家] 已登录:", "手机号后四位" not in body(pg))
    pg.screenshot(path=r"D:\跨境智服\out\buyer_logout_btn.png", full_page=False)
    btn = pg.get_by_role("button", name="退出登录")
    print("[买家] 退出按钮数量:", btn.count())
    if btn.count():
        btn.first.click()
        time.sleep(7)
        print("[买家] 点后回登录页:", "手机号后四位" in body(pg))
        print("[买家] 点后 URL:", pg.url[:90])

    # 商家
    pg2 = b.new_page(viewport={"width": 1440, "height": 1000})
    pg2.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg2.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    pg2.get_by_label("账号").fill("admin")
    pg2.get_by_label("密码").fill("niao2026")
    pg2.get_by_label("密码").press("Enter")
    time.sleep(10)
    print("[商家] 已登录:", "商家后台" in body(pg2))
    pg2.screenshot(path=r"D:\跨境智服\out\shop_logout_btn.png", full_page=False)
    btn2 = pg2.get_by_role("button", name="退出登录")
    print("[商家] 退出按钮数量:", btn2.count())
    if btn2.count():
        btn2.first.click()
        time.sleep(7)
        print("[商家] 点后回登录页:", "账号" in body(pg2) and "密码" in body(pg2))

    b.close()
