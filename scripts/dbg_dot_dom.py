# -*- coding: utf-8 -*-
"""查红点为什么没出来：tab 元素是什么标签、注入的 style 在不在、content 计算值。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"

JS = """() => {
  const tabs = Array.from(document.querySelectorAll('[role="tablist"] [role="tab"]'));
  const out = {n_tabs: tabs.length,
               tags: tabs.map(t => t.tagName + '|' + (t.className||'').toString().slice(0,30)),
               styles: Array.from(document.querySelectorAll('style'))
                        .map(s => (s.textContent||'').includes('nth-of-type(1)::after'))
                        .filter(Boolean).length};
  if (tabs.length) {
    out.content = getComputedStyle(tabs[0], '::after').content;
    out.pos = getComputedStyle(tabs[0]).position;
    out.parent_tag = tabs[0].parentElement.tagName;
  }
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
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
    time.sleep(6)
    print(pg.evaluate(JS))
    print("body 片段:", pg.locator("body").inner_text()[:260].replace("\n", " | "))
    b.close()
