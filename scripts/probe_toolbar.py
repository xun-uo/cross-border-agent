# -*- coding: utf-8 -*-
"""量右上角工具栏的实际占位，用来定页头的 right 值。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"

JS = """() => {
  const pick = (sel) => {
    const el = document.querySelector(sel);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {left: Math.round(r.left), right: Math.round(r.right),
            top: Math.round(r.top), w: Math.round(r.width)};
  };
  const out = {};
  for (const sel of ['[data-testid="stToolbar"]','[data-testid="stAppToolbar"]',
                     '[data-testid="stHeader"]','.shop-head-fixed',
                     '.st-key-lang_box','[data-testid="stDecoration"]']) {
    out[sel] = pick(sel);
  }
  // 工具栏里的按钮
  const tb = document.querySelector('[data-testid="stToolbar"]') ||
             document.querySelector('[data-testid="stAppToolbar"]');
  out.buttons = tb ? [...tb.querySelectorAll('button,a')].map(e => {
    const r = e.getBoundingClientRect();
    return {label: (e.getAttribute('aria-label') || e.title || e.textContent || '').slice(0,18),
            left: Math.round(r.left), w: Math.round(r.width), top: Math.round(r.top)};
  }) : [];
  out.viewport = window.innerWidth;
  return out;
}"""


def run(width, label):
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
        data = pg.evaluate(JS)
        print("=" * 20, label, "宽", width, "=" * 20)
        print(json.dumps(data, ensure_ascii=False, indent=1))
        b.close()


run(1440, "桌面")
run(390, "手机")
