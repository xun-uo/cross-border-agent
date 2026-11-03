# -*- coding: utf-8 -*-
"""窄屏 #28：店名能不能点（点不到 = 被别的元素压住）。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

JS = """() => {
  const a = document.querySelector('.shop-head-fixed a.shop-link, .shop-head-fixed .shop-name');
  if (!a) return 'no-store-name';
  const r = a.getBoundingClientRect();
  const cx = Math.round(r.x + r.width / 2), cy = Math.round(r.y + r.height / 2);
  const top = document.elementFromPoint(cx, cy);
  return {tag: a.tagName, href: a.getAttribute && a.getAttribute('href'),
          rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
          point: {cx, cy},
          hit_tag: top ? top.tagName : null,
          hit_cls: top ? (top.className || '').toString().slice(0, 40) : null,
          hit_is_link: top === a || (a.contains && a.contains(top))};
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    for w, h in [(390, 844), (1440, 950)]:
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto("http://localhost:8502", wait_until="domcontentloaded", timeout=90000)
        time.sleep(8)
        pg.get_by_label("订单号").fill("ORDER20261021001")
        pg.get_by_label("手机号后四位").fill("0001")
        pg.get_by_label("手机号后四位").press("Enter")
        time.sleep(10)
        print(f"[{w}]", pg.evaluate(JS))
        pg.close()
    b.close()
