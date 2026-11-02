# -*- coding: utf-8 -*-
"""补测商家端退出按钮。"""
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
    pg = b.new_page(viewport={"width": 1440, "height": 1000})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    time.sleep(10)
    print("[商家] 登录后 商家后台:", "商家后台" in body(pg))
    print("[商家] 登录后 URL:", pg.url[:80])

    btn = pg.get_by_role("button", name="退出登录")
    print("[商家] 退出按钮数:", btn.count())
    pg.screenshot(path=r"D:\跨境智服\out\shop_logout_before.png", full_page=False)
    btn.first.click()
    time.sleep(8)
    t = body(pg)
    print("[商家] 点后 商家后台还在:", "商家后台" in t)
    print("[商家] 点后 出现登录标题:", "跨境智能客服" in t)
    print("[商家] 点后 URL:", pg.url[:80])
    pg.screenshot(path=r"D:\跨境智服\out\shop_logout_after.png", full_page=False)
    b.close()
