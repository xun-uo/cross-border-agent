# -*- coding: utf-8 -*-
"""商家端 390 宽看一眼：控件有没有叠、tab 行能不能滚。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

JS = """() => {
  const q = s => Array.from(document.querySelectorAll(s)).map(e => {
    const r = e.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)};
  });
  return {head: q('.shop-head-fixed'), lang: q('.st-key-lang_box_shop'),
          out: q('.st-key-shop_logout'), tabs: q('[role="tablist"]')};
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 390, "height": 844})
    pg.goto("http://localhost:8502", wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.locator('[role="tab"]').nth(1).click()
    time.sleep(3)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    for _ in range(20):
        time.sleep(2)
        if pg.locator('[role="tablist"]').count():
            break
    time.sleep(4)
    print(pg.evaluate(JS))
    pg.screenshot(path="D:/跨境智服/out/merchant_390.png")
    b.close()
