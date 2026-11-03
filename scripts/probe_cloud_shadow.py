# -*- coding: utf-8 -*-
"""线上：内容到底藏在哪（shadow DOM？canvas？）。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

JS = """() => {
  const out = {html_len: document.documentElement.outerHTML.length,
               has_text: document.documentElement.outerHTML.includes('订单号'),
               body_children: document.body ? document.body.children.length : -1,
               roots: []};
  const walk = (node, depth) => {
    if (!node || depth > 6) return;
    for (const el of node.querySelectorAll('*')) {
      if (el.shadowRoot) out.roots.push(el.tagName + '#' + (el.id||'') + ' -> shadow children ' + el.shadowRoot.children.length);
    }
  };
  walk(document, 0);
  out.title = document.title;
  out.url = location.href;
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto("https://cross-border-agent.streamlit.app", wait_until="domcontentloaded", timeout=120000)
    time.sleep(20)
    info = pg.evaluate(JS)
    for k, v in info.items():
        print(k, ":", v if k != "roots" else "")
    for r in info["roots"][:10]:
        print("   shadow:", r)
    print("main iframe count:", pg.locator("iframe").count())
    b.close()
