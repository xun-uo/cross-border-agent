# -*- coding: utf-8 -*-
"""第一轮扫描：手机宽度 / 深色模式 / 商家空状态。只截图 + 打印文本特征，不改数据。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"
OUT = r"D:\跨境智服\out"


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


def login_buyer(pg, order="ORDER20261021001", tail="0001"):
    pg.get_by_label("订单号").fill(order)
    pg.get_by_label("手机号后四位").fill(tail)
    pg.get_by_label("手机号后四位").press("Enter")


def login_shop(pg, acct="admin", pwd="niao2026"):
    pg.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    pg.get_by_label("账号").fill(acct)
    pg.get_by_label("密码").fill(pwd)
    pg.get_by_label("密码").press("Enter")


def wait_login(pg, budget=40):
    t0 = time.time()
    while time.time() - t0 < budget:
        b = body(pg)
        if "订单号" not in b or "Niao" in b or "会话" in b:
            return True
        time.sleep(2)
    return False


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)

    # 1) 手机宽度 390 买家
    ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme="light")
    pg = ctx.new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    try:
        login_buyer(pg)
    except Exception as e:
        print("[mobile] login err:", e)
    time.sleep(10)
    t = body(pg)
    print("[mobile] chars=%d login_ok=%s" % (len(t), "订单号" not in t))
    # 横向溢出检测
    ow = pg.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth]")
    print("[mobile] scrollWidth=%s innerWidth=%s" % (ow[0], ow[1]))
    pg.screenshot(path=OUT + r"\scan_mobile_buyer.png", full_page=True)
    ctx.close()

    # 2) 深色模式买家
    ctx = b.new_context(viewport={"width": 1440, "height": 1100}, color_scheme="dark")
    pg = ctx.new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    try:
        login_buyer(pg)
    except Exception as e:
        print("[dark] login err:", e)
    time.sleep(10)
    pg.screenshot(path=OUT + r"\scan_dark_buyer.png", full_page=False)
    print("[dark] shot ok")
    ctx.close()

    # 3) 商家端空状态（没有会话时的会话列表）
    ctx = b.new_context(viewport={"width": 1440, "height": 1100}, color_scheme="light")
    pg = ctx.new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    try:
        login_shop(pg)
    except Exception as e:
        print("[shop] login err:", e)
    time.sleep(10)
    t = body(pg)
    print("[shop] chars=%d" % len(t))
    print("[shop] tabs:", [x.inner_text() for x in pg.get_by_role("tab").all()])
    pg.screenshot(path=OUT + r"\scan_shop_empty.png", full_page=False)
    ctx.close()

    b.close()
