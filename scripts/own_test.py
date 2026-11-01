# -*- coding: utf-8 -*-
"""端到端验证接管归属：admin 接手后 judge 看不到；judge 接手后 admin 看不到。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"
OUT = r"D:\跨境智服\out"


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


def shop_login(browser, acct, pwd):
    ctx = browser.new_context(viewport={"width": 1100, "height": 1000})
    pg = ctx.new_page()
    pg.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(5)
    pg.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    pg.get_by_label("账号").fill(acct)
    pg.get_by_label("密码").fill(pwd)
    pg.get_by_label("密码").press("Enter")
    time.sleep(7)
    return pg


def open_first(pg):
    for name in ("展开", "查看"):
        try:
            pg.get_by_role("button", name=name).first.click(timeout=3000)
            time.sleep(2)
        except Exception:
            pass


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)

    # 1) 买家转人工
    ctx_b = browser.new_context(viewport={"width": 900, "height": 900})
    buyer = ctx_b.new_page()
    buyer.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(5)
    buyer.get_by_label("订单号").fill("ORDER20261021001")
    buyer.get_by_label("手机号后四位").fill("0001")
    buyer.get_by_label("手机号后四位").press("Enter")
    time.sleep(6)
    box = buyer.get_by_placeholder(re.compile("输入你的问题"))
    box.fill("转人工")
    box.press("Enter")
    time.sleep(6)
    print("买家已转人工")

    # 2) admin 接手
    admin = shop_login(browser, "admin", "niao2026")
    open_first(admin)
    rb = admin.get_by_placeholder(re.compile("以人工客服身份回复"))
    rb.fill("我是 admin，正在帮您处理。")
    rb.press("Enter")
    time.sleep(7)
    t = body(admin)
    print("admin 回复后页面含接管标记:", "已由" in t and "admin" in t)
    admin.screenshot(path=rf"{OUT}\own_admin.png", full_page=True)

    # 3) judge 登录，应该看不到这个会话
    judge = shop_login(browser, "judge", "xinghe2026")
    time.sleep(4)
    tj = body(judge)
    print("judge 看不到被接管的会话:", "会话" not in tj or "暂无进行中" in tj)
    judge.screenshot(path=rf"{OUT}\own_judge.png", full_page=True)

    browser.close()
