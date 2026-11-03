# -*- coding: utf-8 -*-
"""线上首页到底是什么状态（冷启动/唤醒/正常）。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto("https://cross-border-agent.streamlit.app", wait_until="domcontentloaded", timeout=120000)
    for i in range(6):
        time.sleep(8)
        txt = pg.locator("body").inner_text()
        print(f"--- t={8*(i+1)}s ---")
        print(txt[:400].replace("\n", " | "))
        pg.screenshot(path=f"D:/跨境智服/out/cloud_home_{i}.png")
        if "订单号" in txt:
            print("登录表单已出现")
            break
    b.close()
