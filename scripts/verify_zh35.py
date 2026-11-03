# -*- coding: utf-8 -*-
"""验 #35：商家端「翻译成中文」按钮 —— 西语会话翻出中文对照。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"


def buyer_login(pg):
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(9)


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)

    bp = b.new_page(viewport={"width": 1440, "height": 950})
    buyer_login(bp)
    # 转人工
    bp.locator('input[type="file"]').first.set_input_files("D:/跨境智服/out/test_upload.png")
    time.sleep(3)
    bp.locator('[data-testid="stChatInput"] button[aria-label="Send message"]').first.click()
    time.sleep(12)

    # 切西班牙语
    bp.locator('[data-testid="stSelectbox"]').first.click()
    time.sleep(1.5)
    bp.locator('[role="option"]').filter(has_text="Español").last.click()
    time.sleep(8)
    # 人工模式下发一句西语
    box = bp.locator('[data-testid="stChatInput"] textarea').first
    box.fill("¿Cuál es la política de devoluciones?")
    box.press("Enter")
    time.sleep(12)
    print("买家页有西语吗:", "¿Cuál" in bp.locator("body").inner_text())

    mp = b.new_page(viewport={"width": 1440, "height": 950})
    mp.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    mp.locator('[role="tab"]').nth(1).click()
    time.sleep(3)
    mp.get_by_label("账号").fill("admin")
    mp.get_by_label("密码").fill("niao2026")
    mp.get_by_label("密码").press("Enter")
    for _ in range(20):
        time.sleep(2)
        if mp.locator('[role="tablist"]').count():
            break
    time.sleep(5)
    print("会话里有西语原文:", "¿Cuál" in mp.locator("body").inner_text())

    mp.get_by_role("button", name="查看").first.click()
    time.sleep(8)
    mp.screenshot(path="D:/跨境智服/out/zh35_before.png")

    btn = mp.get_by_role("button", name="翻译成中文")
    print("翻译按钮:", btn.count())
    btn.first.click()
    time.sleep(18)
    tt = mp.locator(".zh-trans")
    print("译文块数:", tt.count())
    for i in range(tt.count()):
        print("  译文:", tt.nth(i).inner_text()[:120])
    mp.screenshot(path="D:/跨境智服/out/zh35_after.png")
    b.close()
