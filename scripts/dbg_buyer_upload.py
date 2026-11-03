# -*- coding: utf-8 -*-
"""调试：买家端图片上传按钮怎么触发。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(10)
    print("file input 数:", pg.locator('input[type="file"]').count())
    print("chat input 区按钮:", [x for x in pg.locator('[data-testid="stChatInput"] button').all_inner_texts()])
    print("aria 按钮:", pg.locator('[data-testid="stChatInput"] button').evaluate_all(
        "els => els.map(e => e.getAttribute('aria-label') || e.title || '')"))
    # 试试点开启上传
    try:
        pg.locator('[data-testid="stChatInput"] button').first.click()
        time.sleep(2)
        print("点第一个按钮后 file input 数:", pg.locator('input[type="file"]').count())
    except Exception as e:
        print("点按钮失败:", e)
    pg.locator('input[type="file"]').first.set_input_files("D:/跨境智服/out/test_upload.png")
    time.sleep(15)
    print("上传后 body:", pg.locator("body").inner_text()[:600].replace("\n", " | "))
    pg.screenshot(path="D:/跨境智服/out/dbg_upload.png")
    b.close()
