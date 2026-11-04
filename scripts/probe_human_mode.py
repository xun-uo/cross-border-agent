# -*- coding: utf-8 -*-
"""复现：买家先发「人工」→ 再发「你好」，人工模式下 AI 还在不在回话。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"


def send(pg, text):
    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill(text)
    box.press("Enter")
    for _ in range(20):
        time.sleep(2)
        if pg.locator(".busy-pill").count() == 0:
            break
    time.sleep(3)


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021006")
    pg.get_by_label("手机号后四位").fill("0006")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(10)

    send(pg, "人工")
    body1 = pg.locator("body").inner_text()
    print("[人工] 有「我请同事」:", "我请同事" in body1)
    print("[人工] 有等待文案:", "正在等待商家回复" in body1)
    print("[人工] 页头状态:", [ln for ln in body1.split("\n") if "在线" in ln][:1])

    send(pg, "你好")
    time.sleep(6)
    body2 = pg.locator("body").inner_text()
    print("[你好] 有 AI 回复「有什么可以帮您」:", "有什么可以帮您" in body2)
    print("[你好] 有等待文案:", "正在等待商家回复" in body2)
    print("[你好] 气泡:")
    for x in pg.locator('[data-testid="stChatMessage"]').all():
        print("   ", x.inner_text().replace("\n", " ")[:80])
    pg.screenshot(path="D:/跨境智服/out/human_mode.png")
    b.close()
