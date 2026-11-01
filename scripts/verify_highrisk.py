# -*- coding: utf-8 -*-
"""验「高危对话」：先造一条会被判 rewrite/block 的对话，再看会话记录 tab。"""
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

    # 买家：问两个问题，一个正常、一个踩线
    ctx1 = b.new_context(viewport={"width": 1280, "height": 900})
    pg1 = ctx1.new_page()
    pg1.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg1.get_by_label("订单号").fill("ORDER20261021001")
    pg1.get_by_label("手机号后四位").fill("0001")
    pg1.get_by_label("手机号后四位").press("Enter")
    time.sleep(9)

    box = pg1.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单到哪了")
    box.press("Enter")
    time.sleep(15)

    box = pg1.locator('[data-testid="stChatInput"] textarea').first
    box.fill("你们这个面霜能彻底治好我的痘痘吗，保证有效吗")
    box.press("Enter")
    time.sleep(18)
    ctx1.close()

    # 商家：看会话记录
    ctx2 = b.new_context(viewport={"width": 1440, "height": 1100})
    pg = ctx2.new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    time.sleep(10)

    pg.get_by_role("tab", name="会话记录").click(timeout=8000)
    time.sleep(5)
    t = body(pg)
    print("含『高危对话』:", "高危对话" in t)
    print("含『问答流水』:", "问答流水" in t)
    # 抓那段说明文字
    for ln in t.splitlines():
        if "轮" in ln and ("拦截" in ln or "改写" in ln or "暂无" in ln):
            print("说明行:", ln[:90])
    pg.screenshot(path=r"D:\跨境智服\out\verify_highrisk.png", full_page=False)
    b.close()
