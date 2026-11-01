# -*- coding: utf-8 -*-
"""线上：登录商家 → 展开侧栏 → 抓 build 号，确认是不是 #110。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "https://cross-border-agent.streamlit.app"


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 1100})
    pg = ctx.new_page()
    pg.goto(URL, timeout=120000, wait_until="domcontentloaded")

    for _ in range(60):
        if "订单号" in body(pg):
            break
        time.sleep(5)
    print("login page:", "订单号" in body(pg))

    try:
        pg.get_by_role("tab", name="商家").click(timeout=10000)
        time.sleep(2)
        pg.get_by_label("账号").fill("admin")
        pg.get_by_label("密码").fill("niao2026")
        pg.get_by_label("密码").press("Enter")
    except Exception as e:
        print("login fail:", e)

    for _ in range(30):
        time.sleep(2)
        if "待处理会话" in body(pg) or "会话" in body(pg):
            break
    print("logged in:", "商家后台" in body(pg))

    for sel in ('[data-testid="stSidebarCollapsedControl"]',):
        try:
            pg.locator(sel).click(timeout=4000)
            time.sleep(3)
        except Exception:
            pass

    t = body(pg)
    m = re.search(r"build[^\n]*", t, re.I)
    print("BUILD:", m.group(0).strip() if m else "not found")
    pg.screenshot(path=r"D:\跨境智服\out\online_build.png", full_page=False)
    b.close()
