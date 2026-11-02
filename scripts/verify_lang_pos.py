# -*- coding: utf-8 -*-
"""验语言下拉的位置：应在工具栏左侧，不重叠。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

JS = """() => {
  const e = document.querySelector('.st-key-lang_box');
  if (!e) return null;
  const r = e.getBoundingClientRect();
  return {left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top)};
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto("http://localhost:8502", wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(9)
    d = pg.evaluate(JS)
    limit = 1440 - 216
    print("语言下拉:", d, "| 工具栏左界", limit,
          "| 不重叠:", d is not None and d["right"] <= limit)
    pg.screenshot(path=r"D:\跨境智服\out\after_lang_move.png", full_page=False)
    b.close()
