# -*- coding: utf-8 -*-
"""验页头右边界不再压住右上角工具栏。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

JS = """() => {
  const h = document.querySelector('.shop-head-fixed');
  const hr = h ? h.getBoundingClientRect() : null;
  return {headRight: hr ? Math.round(hr.right) : null, viewport: window.innerWidth};
}"""


def run(b, w, who):
    pg = b.new_page(viewport={"width": w, "height": 950})
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
    d = pg.evaluate(JS)
    limit = d["viewport"] - 216
    print("%-6s 宽%-5d 页头右边界 %-5s 工具栏左界 %-5s 不重叠 %s"
          % (who, w, d["headRight"], limit, d["headRight"] is not None and d["headRight"] <= limit))
    pg.screenshot(path=r"D:\跨境智服\out\head_%s_%d.png" % (who, w),
                  clip={"x": d["viewport"] - 460, "y": 0, "width": 460, "height": 90})
    pg.close()


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    run(b, 1919, "buyer")
    run(b, 1919, "shop")
    run(b, 1440, "buyer")
    b.close()
