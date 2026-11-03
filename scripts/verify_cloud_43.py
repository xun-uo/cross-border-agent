# -*- coding: utf-8 -*-
"""线上复核 #43：前面已答过物流，接着问产品功效 / 追问，回复里不该再塞物流。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CLOUD = "https://cross-border-agent.streamlit.app"
LOGISTIC = ("运单", "承运商", "YunExpress", "CN2026", "预计送达", "在途", "分拣中心", "物流")


def app_frame(pg, wait=120):
    t0 = time.time()
    while time.time() - t0 < wait:
        for f in pg.frames:
            if f is pg.main_frame:
                continue
            try:
                if f.locator('[data-testid="stApp"]').count():
                    return f
            except Exception:
                pass
        time.sleep(2)
    return None


def ask(pg, text, tag):
    f = app_frame(pg)
    box = f.locator('[data-testid="stChatInput"] textarea').first
    box.fill(text)
    box.press("Enter")
    last = ""
    for _ in range(24):
        time.sleep(3)
        f = app_frame(pg)
        try:
            if f.get_by_text("正在处理").count() == 0:
                bubbles = f.locator('[data-testid="stChatMessage"]')
                if bubbles.count() >= 2:
                    last = bubbles.last.inner_text().replace("\n", " ")
                    break
        except Exception:
            pass
    hit = [w for w in LOGISTIC if w in last]
    print(f"[{tag}] 问: {text}")
    print(f"      答: {last[:200]}")
    print(f"      含物流词: {hit}")


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(CLOUD, wait_until="domcontentloaded", timeout=120000)
    f = app_frame(pg)
    for _ in range(40):
        time.sleep(3)
        try:
            if f.get_by_label("订单号").count():
                break
        except Exception:
            pass
    f.get_by_label("订单号").fill("ORDER20261021001")
    f.get_by_label("手机号后四位").fill("0001")
    f.get_by_label("手机号后四位").press("Enter")
    time.sleep(14)
    ask(pg, "这个面霜能去黑头吗", "产品功效")
    ask(pg, "那能干嘛", "追问")
    b.close()
