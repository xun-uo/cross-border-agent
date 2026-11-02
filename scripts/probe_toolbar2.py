# -*- coding: utf-8 -*-
"""精确列出右上角所有可见图标的位置，用来定页头的 right 值。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"

JS = """() => {
  const header = document.querySelector('[data-testid="stHeader"]');
  if (!header) return {err: 'no header'};
  const items = [];
  for (const e of header.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width < 12 || r.height < 12 || r.top > 70) continue;
    const label = (e.getAttribute('aria-label') || e.title || e.textContent || '').trim().slice(0, 24);
    items.push({tag: e.tagName.toLowerCase(), label,
                left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top)});
  }
  // 只留最外层或带 label 的
  const uniq = [];
  const seen = new Set();
  for (const it of items) {
    const k = it.left + ':' + it.right + ':' + it.label;
    if (seen.has(k)) continue;
    seen.add(k);
    uniq.push(it);
  }
  return {viewport: window.innerWidth, items: uniq.sort((a,b)=>a.left-b.left)};
}"""


def run(width):
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True)
        ctx = b.new_context(viewport={"width": width, "height": 950})
        pg = ctx.new_page()
        pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
        time.sleep(8)
        pg.get_by_label("订单号").fill("ORDER20261021001")
        pg.get_by_label("手机号后四位").fill("0001")
        pg.get_by_label("手机号后四位").press("Enter")
        time.sleep(9)
        import json
        d = pg.evaluate(JS)
        print("=" * 18, "宽", width, "=" * 18)
        print(json.dumps(d, ensure_ascii=False, indent=1))
        b.close()


run(1919)
