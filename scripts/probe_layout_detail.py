# -*- coding: utf-8 -*-
"""看内容区里到底谁占着高度（页头下面那 96px 空隙）。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"

JS = """() => {
  const root = document.querySelector('[data-testid="stMainBlockContainer"]');
  if (!root) return [];
  const rows = [];
  const walk = (el, depth) => {
    if (depth > 3) return;
    for (const c of el.children) {
      const r = c.getBoundingClientRect();
      rows.push({d: depth, tag: c.tagName.toLowerCase(),
                 tid: c.getAttribute('data-testid') || '',
                 cls: (c.className||'').toString().slice(0,42),
                 y: Math.round(r.y), h: Math.round(r.height),
                 txt: (c.innerText||'').replace(/\\n/g,' ').slice(0,26)});
      walk(c, depth + 1);
    }
  };
  walk(root, 0);
  return rows.filter(r => r.h > 0).slice(0, 26);
}"""


def report(pg, tag):
    print(f"===== {tag} =====")
    for r in pg.evaluate(JS):
        print(f"  d{r['d']} y={r['y']:>4} h={r['h']:>4} {r['tag']:<8} {r['tid']:<22} {r['txt']!r}")


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg.get_by_text("商家", exact=True).first.click()
    time.sleep(3)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    time.sleep(11)
    report(pg, "商家 1440")

    pg2 = b.new_page(viewport={"width": 1440, "height": 950})
    pg2.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg2.get_by_label("订单号").fill("ORDER20261021001")
    pg2.get_by_label("手机号后四位").fill("0001")
    pg2.get_by_label("手机号后四位").press("Enter")
    time.sleep(10)
    report(pg2, "买家 1440")
    b.close()
