# -*- coding: utf-8 -*-
"""验 #49：纯图不转人工、图+要办的事才转人工。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"
IMG = "D:/跨境智服/out/test_upload.png"


def upload(pg, with_text=""):
    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.click()
    if with_text:
        box.fill(with_text)
    pg.locator('input[type="file"]').first.set_input_files(IMG)
    time.sleep(3)
    snd = pg.locator('[data-testid="stChatInput"] button[aria-label="Send message"]')
    if snd.count():
        snd.first.click()
    else:
        box.press("Enter")
    time.sleep(12)


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021004")
    pg.get_by_label("手机号后四位").fill("0004")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(10)

    # --- 纯图：不该转人工 ---
    upload(pg)
    body = pg.locator("body").inner_text()
    print("[纯图] 有补充说明提示:", "补一句说明" in body)
    print("[纯图] 是否转人工(页面出现等待文案):", "正在等待商家回复" in body)
    print("[纯图] 是否出现旧文案「已转人工客服处理」:", "已转人工客服处理" in body)
    pg.screenshot(path="D:/跨境智服/out/img49_pure.png")

    # --- 图 + 要办的事：应该转人工 ---
    upload(pg, "外包装破了，能退吗")
    time.sleep(6)
    body2 = pg.locator("body").inner_text()
    print("[图+文字] 是否转人工:", "正在等待商家回复" in body2 or "请同事来协助" in body2)
    pg.screenshot(path="D:/跨境智服/out/img49_with_text.png")
    b.close()
