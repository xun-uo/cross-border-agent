# -*- coding: utf-8 -*-
"""量页头 / 语言下拉 / 退出按钮的实际位置（桌面 + 手机宽度），买家端和商家端各一次。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"

JS = """(sel) => {
  const out = [];
  document.querySelectorAll(sel).forEach((el, i) => {
    const r = el.getBoundingClientRect();
    out.push({i, cls: (el.className || '').toString().slice(0, 60),
              x: Math.round(r.x), y: Math.round(r.y),
              w: Math.round(r.width), h: Math.round(r.height),
              txt: (el.innerText || '').replace(/\\n/g, ' ').slice(0, 40)});
  });
  return out;
}"""


def dump(pg, tag):
    print(f"===== {tag} =====")
    print("  head:", pg.evaluate(JS, ".shop-head-fixed"))
    print("  langbox:", pg.evaluate(JS, ".st-key-lang_box, .st-key-lang_box_shop, .st-key-lang_box_login"))
    print("  logout:", pg.evaluate(JS, ".st-key-buyer_logout, .st-key-shop_logout"))
    print("  tabs:", pg.evaluate(JS, '[role="tablist"]'))
    print("  main container:", pg.evaluate(JS, '[data-testid="stMainBlockContainer"]'))
    print("  first children:",
          pg.evaluate("""() => Array.from(document.querySelectorAll('[data-testid="stMainBlockContainer"] > div')).slice(0,8).map(d => {
              const r = d.getBoundingClientRect();
              return {y: Math.round(r.y), h: Math.round(r.height), cls: (d.className||'').toString().slice(0,50), txt: (d.innerText||'').replace(/\\n/g,' ').slice(0,30)};
          })"""))


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)

    for w, h, tag in [(1440, 950, "买家 1440"), (390, 844, "买家 390")]:
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
        time.sleep(7)
        pg.get_by_label("订单号").fill("ORDER20261021001")
        pg.get_by_label("手机号后四位").fill("0001")
        pg.get_by_label("手机号后四位").press("Enter")
        time.sleep(9)
        dump(pg, tag)
        pg.screenshot(path=f"D:/跨境智服/out/pos_buyer_{w}.png", full_page=False)
        pg.close()

    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg.get_by_text("商家", exact=True).first.click()
    time.sleep(3)
    try:
        pg.get_by_label("账号").fill("admin")
        pg.get_by_label("密码").fill("niao2026")
        pg.get_by_label("密码").press("Enter")
    except Exception as e:
        print("商家登录控件没找到:", e)
        print(pg.locator("body").inner_text()[:300])
    time.sleep(10)
    dump(pg, "商家 1440")
    pg.screenshot(path="D:/跨境智服/out/pos_merchant_1440.png", full_page=False)
    pg.close()
    b.close()
