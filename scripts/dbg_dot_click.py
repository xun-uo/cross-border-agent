# -*- coding: utf-8 -*-
"""点开会话后红点为什么不清：点完连看 15 秒的 dot 和 DOTDBG。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DOT_JS = """() => {
  const b = document.querySelectorAll('[role="tablist"] [role="tab"]')[0];
  if (!b) return 'no-tab';
  const c = getComputedStyle(b, '::after').content;
  return (c && c !== 'none' && c !== 'normal') ? c : 'none';
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    bp = b.new_page(viewport={"width": 1440, "height": 950})
    bp.goto("http://localhost:8502", wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    bp.get_by_label("订单号").fill("ORDER20261021001")
    bp.get_by_label("手机号后四位").fill("0001")
    bp.get_by_label("手机号后四位").press("Enter")
    time.sleep(9)
    bp.locator('input[type="file"]').first.set_input_files("D:/跨境智服/out/test_upload.png")
    time.sleep(3)
    bp.locator('[data-testid="stChatInput"] button[aria-label="Send message"]').first.click()
    time.sleep(14)

    mp = b.new_page(viewport={"width": 1440, "height": 950})
    mp.goto("http://localhost:8502", wait_until="domcontentloaded", timeout=90000)
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
    time.sleep(4)
    print("点前 dot:", mp.evaluate(DOT_JS))
    btn = mp.get_by_role("button", name="查看")
    print("查看按钮:", btn.count())
    btn.first.click()
    for i in range(6):
        time.sleep(3)
        dbg = [x for x in mp.locator("body").inner_text().split("\n") if "DOTDBG" in x]
        print(f"  +{3*(i+1)}s dot={mp.evaluate(DOT_JS)} {dbg[:1]}")
    b.close()
