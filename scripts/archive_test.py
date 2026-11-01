# -*- coding: utf-8 -*-
"""验证：结束会话后，这段对话会归档到「会话记录」并且能重新打开。"""
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

    # 1) 买家转人工 + 追问一句
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

    # 2) admin 回复 → 结束会话
    ctx_s = browser.new_context(viewport={"width": 1100, "height": 1000})
    admin = ctx_s.new_page()
    admin.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(5)
    admin.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    admin.get_by_label("账号").fill("admin")
    admin.get_by_label("密码").fill("niao2026")
    admin.get_by_label("密码").press("Enter")
    time.sleep(7)
    for name in ("展开", "查看"):
        try:
            admin.get_by_role("button", name=name).first.click(timeout=3000)
            time.sleep(2)
        except Exception:
            pass
    rb = admin.get_by_placeholder(re.compile("以人工客服身份回复"))
    rb.fill("已经帮你催了，明天到。")
    rb.press("Enter")
    time.sleep(7)

    try:
        admin.get_by_role("button", name=re.compile("结束会话")).first.click(timeout=4000)
        time.sleep(5)
        print("点了结束会话")
    except Exception as e:
        print("结束会话按钮:", e)

    # 结束之后待处理列表应该是空的
    admin.get_by_role("tab", name="待处理会话").click()
    time.sleep(4)
    _pt = body(admin)
    print("结束后待处理会话已清空:", "暂无进行中的人工会话" in _pt)

    # 3) 切到会话记录，看归档
    admin.get_by_role("tab", name="会话记录").click()
    time.sleep(3)
    try:
        admin.get_by_role("button", name="刷新").first.click(timeout=4000)
        time.sleep(5)
    except Exception as e:
        print("刷新:", e)
    t = body(admin)
    print("归档里有历史会话:", "历史会话" in t)
    print("标记为人工处理过:", "人工处理过" in t)
    print("点开前可见「查看」:", "查看" in t)
    admin.screenshot(path=rf"{OUT}\archive_list.png", full_page=True)

    try:
        admin.get_by_role("button", name="查看").first.click(timeout=4000)
        time.sleep(4)
        t2 = body(admin)
        print("打开后能看到买家原话:", "转人工" in t2)
        print("打开后能看到人工回复:", "明天到" in t2)
        admin.screenshot(path=rf"{OUT}\archive_open.png", full_page=True)
    except Exception as e:
        print("打开失败:", e)

    browser.close()
