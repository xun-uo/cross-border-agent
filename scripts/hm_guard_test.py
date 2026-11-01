# -*- coding: utf-8 -*-
"""测商家发红线话术会被拦住。"""
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


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)

    # 买家转人工
    ctx_b = browser.new_context(viewport={"width": 900, "height": 1000})
    buyer = ctx_b.new_page()
    buyer.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(6)
    buyer.get_by_label("订单号").fill("ORDER20261021001")
    buyer.get_by_label("手机号后四位").fill("0001")
    buyer.get_by_label("手机号后四位").press("Enter")
    time.sleep(6)
    box = buyer.get_by_placeholder(re.compile("输入你的问题"))
    box.fill("转人工")
    box.press("Enter")
    time.sleep(6)

    # 商家
    ctx_s = browser.new_context(viewport={"width": 1200, "height": 1000})
    shop = ctx_s.new_page()
    shop.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(6)
    shop.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    shop.get_by_label("账号").fill("admin")
    shop.get_by_label("密码").fill("niao2026")
    shop.get_by_label("密码").press("Enter")
    time.sleep(7)
    try:
        shop.get_by_role("button", name="查看").first.click(timeout=4000)
        time.sleep(4)
    except Exception as e:
        print("expand:", e)

    # 发红线话术
    rb = shop.get_by_placeholder(re.compile("以人工客服身份回复"))
    rb.click()
    rb.fill("绝对治疗疾病")
    rb.press("Enter")
    time.sleep(3)

    t = body(shop)
    blocked = "这句话没发出去" in t
    print("红线话术被拦截:", blocked)
    if blocked:
        for line in t.splitlines():
            if "命中" in line or "原话" in line or "没发出去" in line:
                print("  ", line.strip()[:120])
    shop.screenshot(path=rf"{OUT}\guard_block.png", full_page=True)

    # 再发一句正常话术，应该能发出去
    rb2 = shop.get_by_placeholder(re.compile("以人工客服身份回复"))
    rb2.click()
    rb2.fill("已经帮您查了，今天下午派送。")
    rb2.press("Enter")
    time.sleep(7)
    t2 = body(shop)
    print("正常话术已发出:", "已发送。买家会在 4 秒内自动收到" in t2 or "人工" in t2)
    shop.screenshot(path=rf"{OUT}\guard_pass.png", full_page=True)

    browser.close()
