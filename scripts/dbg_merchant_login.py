# -*- coding: utf-8 -*-
"""调试：商家登录到底成没成、买家发图有没有转人工。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    mp = b.new_page(viewport={"width": 1440, "height": 950})
    mp.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    print("登录页 tabs:", mp.locator('[role="tab"]').all_inner_texts())
    mp.locator('[role="tab"]').nth(1).click()
    time.sleep(3)
    print("切到商家后标签:", mp.locator("body").inner_text()[:300].replace("\n", " | "))
    for lb in ("账号", "密码"):
        try:
            mp.get_by_label(lb).fill("admin" if lb == "账号" else "niao2026")
        except Exception as e:
            print(f"填 {lb} 失败:", e)
    mp.get_by_label("密码").press("Enter")
    time.sleep(12)
    print("登录后 body:", mp.locator("body").inner_text()[:400].replace("\n", " | "))
    print("有 tablist 吗:", mp.locator('[role="tablist"]').count())
    print("按钮:", [x for x in mp.locator("button").all_inner_texts()][:12])
    mp.screenshot(path="D:/跨境智服/out/dbg_merchant.png")
    b.close()
