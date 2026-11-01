# -*- coding: utf-8 -*-
"""验证：买家发完消息后刷新页面，聊天记录还能捞回来。"""
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
    ctx = browser.new_context(viewport={"width": 1000, "height": 1000})
    pg = ctx.new_page()
    pg.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(6)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(7)

    url = pg.url
    print("登录后 URL 带 sid:", "sid=" in url)

    box = pg.get_by_placeholder(re.compile("输入你的问题"))
    box.fill("我的订单在哪")
    box.press("Enter")
    time.sleep(12)

    before = body(pg)
    print("刷新前有提问:", "我的订单在哪" in before)
    print("刷新前有回答:", "ORDER20261021001" in before and "承运商" in before)
    pg.screenshot(path=rf"{OUT}\restore_before.png", full_page=True)

    # 刷新（等于买家重进）
    pg.reload(wait_until="domcontentloaded")
    time.sleep(10)

    after = body(pg)
    print("---- 刷新后 ----")
    print("记录还在（提问）:", "我的订单在哪" in after)
    print("记录还在（回答）:", "承运商" in after)
    print("没有回到空白欢迎页:", "你好，我是这家店的客服助手" not in after
          or "我的订单在哪" in after)
    pg.screenshot(path=rf"{OUT}\restore_after.png", full_page=True)

    # 再发一条，确认恢复后还能继续聊
    try:
        box2 = pg.get_by_placeholder(re.compile("输入你的问题"))
        box2.fill("那大概什么时候到")
        box2.press("Enter")
        time.sleep(12)
        t3 = body(pg)
        print("恢复后继续对话可用:", "大概什么时候到" in t3)
    except Exception as e:
        print("继续对话失败:", e)

    browser.close()
