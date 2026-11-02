# -*- coding: utf-8 -*-
"""查 Streamlit 内容容器的实际选择器和 padding。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

JS = """() => {
  const sels = ['.block-container', '[data-testid="stAppViewBlockContainer"]',
                '[data-testid="stMainBlockContainer"]', '[data-testid="stMain"]',
                'section.main', '.main', '[data-testid="stAppViewContainer"]'];
  const out = [];
  for (const s of sels) {
    const el = document.querySelector(s);
    if (!el) { out.push([s, 'NOT FOUND']); continue; }
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    out.push([s, 'pt=' + cs.paddingTop, 'top=' + Math.round(r.top), 'w=' + Math.round(r.width)]);
  }
  // 再列一下所有带 block 相关 testid 的
  const ids = new Set();
  for (const e of document.querySelectorAll('[data-testid]')) {
    const t = e.getAttribute('data-testid');
    if (/block|main|appview/i.test(t)) ids.add(t);
  }
  return {sels: out, testids: [...ids]};
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
    for s in d["sels"]:
        print("  ", s)
    print("相关 testid:", d["testids"])
    # 语言下拉的实际位置
    box = pg.evaluate("""() => {
      const e = document.querySelector('.st-key-lang_box');
      if (!e) return null;
      const r = e.getBoundingClientRect();
      return {top: Math.round(r.top), left: Math.round(r.left)};
    }""")
    print("语言下拉位置:", box)
    b.close()
