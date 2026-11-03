# -*- coding: utf-8 -*-
"""验移动端：店名能否点击、控件位置；再确认桌面端没被破坏。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HIT_JS = """() => {
  const a = document.querySelector('a.shop-link') || document.querySelector('.shop-name');
  if (!a) return {err: 'no shop name'};
  const r = a.getBoundingClientRect();
  const cx = Math.round(r.left + r.width / 2);
  const cy = Math.round(r.top + r.height / 2);
  const top = document.elementFromPoint(cx, cy);
  return {
    rect: {left: Math.round(r.left), right: Math.round(r.right),
           top: Math.round(r.top), bottom: Math.round(r.bottom)},
    center: [cx, cy],
    topElTag: top ? top.tagName.toLowerCase() : null,
    topElClass: top ? (top.className || '').toString().slice(0, 60) : null,
    isSelfOrChild: top ? (a === top || a.contains(top)) : false
  };
}"""


def check(b, width, who):
    pg = b.new_page(viewport={"width": width, "height": 900})
    pg.goto("http://localhost:8502", wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    if who == "buyer":
        pg.get_by_label("订单号").fill("ORDER20261021001")
        pg.get_by_label("手机号后四位").fill("0001")
        pg.get_by_label("手机号后四位").press("Enter")
    else:
        pg.get_by_role("tab", name="商家").click()
        time.sleep(1.5)
        pg.get_by_label("账号").fill("admin")
        pg.get_by_label("密码").fill("niao2026")
        pg.get_by_label("密码").press("Enter")
    time.sleep(9)
    d = pg.evaluate(HIT_JS)
    print("宽%-4d %-6s 店名可点击=%s  center=%s  命中元素=%s(.%s)"
          % (width, who, d.get("isSelfOrChild"), d.get("center"),
             d.get("topElTag"), d.get("topElClass")))
    pg.screenshot(path=r"D:\跨境智服\out\resp_%s_%d.png" % (who, width),
                  full_page=False)
    pg.close()


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    for w in (390, 768, 1440):
        check(b, w, "buyer")
    check(b, 390, "shop")
    b.close()
