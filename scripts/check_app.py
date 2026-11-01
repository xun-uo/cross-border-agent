# -*- coding: utf-8 -*-
"""打开演示站 → 登录 → 抓 build 号 + 截图。

用法： python check_app.py [url] [name] [buyer|shop]
只读：不点发送、不改数据。
"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"
NAME = sys.argv[2] if len(sys.argv) > 2 else "local"
ROLE = sys.argv[3] if len(sys.argv) > 3 else "buyer"
SCHEME = sys.argv[4] if len(sys.argv) > 4 else "light"
SHOT = rf"D:\跨境智服\out\app_{NAME}_{ROLE}.png"


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


def wake_and_wait(pg, budget=150):
    start = time.time()
    while time.time() - start < budget:
        if "订单号" in body(pg):
            return True
        for lbl in ("get this app back up", "Yes, get this app back up"):
            try:
                pg.get_by_text(lbl, exact=False).first.click(timeout=800)
                print("[wake] clicked")
                break
            except Exception:
                pass
        time.sleep(3)
    return False


def login(pg):
    # 表单里按回车即提交，比找按钮稳（买卖两边的提交按钮都叫「进入」）
    if ROLE == "shop":
        pg.get_by_role("tab", name="商家").click()
        time.sleep(1.5)
        pg.get_by_label("账号").fill("admin")
        pg.get_by_label("密码").fill("niao2026")
        pg.get_by_label("密码").press("Enter")
    else:
        pg.get_by_label("订单号").fill("ORDER20261021001")
        pg.get_by_label("手机号后四位").fill("0001")
        pg.get_by_label("手机号后四位").press("Enter")


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 1100},
                              color_scheme=SCHEME)
    page = ctx.new_page()
    page.goto(URL, timeout=120000, wait_until="domcontentloaded")

    if not wake_and_wait(page):
        print(f"login page NOT rendered (body len {len(body(page))})")
        page.screenshot(path=SHOT, full_page=True)
        print("shot:", SHOT)
        browser.close()
        sys.exit(2)

    login(page)

    logged = False
    for _ in range(30):
        time.sleep(2)
        if page.get_by_placeholder(re.compile("输入你的问题|回复")).count() > 0 or \
           "会话" in body(page) or "Niao Store" in body(page):
            logged = True
            break

    time.sleep(3)
    try:
        page.locator('[data-testid="stSidebarCollapsedControl"]').click(timeout=3000)
        time.sleep(2)
    except Exception:
        pass

    t = body(page)
    m = re.search(r"build[^\n]*", t, re.I)
    print(f"role={ROLE} logged_in={logged}")
    print("BUILD :", m.group(0).strip() if m else "not visible")
    page.screenshot(path=SHOT, full_page=True)
    print("shot  :", SHOT)
    browser.close()
