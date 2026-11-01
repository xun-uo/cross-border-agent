# -*- coding: utf-8 -*-
"""探测 Streamlit 页面里可用的主题 CSS 变量，用来给粘性页头取背景色。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"

JS = """
() => {
  const out = {};
  const roots = {
    'html': document.documentElement,
    'body': document.body,
    'stApp': document.querySelector('[data-testid="stApp"]'),
    'stAppViewContainer': document.querySelector('[data-testid="stAppViewContainer"]'),
    'blockContainer': document.querySelector('[data-testid="stMainBlockContainer"]'),
  };
  for (const [k, el] of Object.entries(roots)) {
    if (!el) { out[k] = null; continue; }
    const cs = getComputedStyle(el);
    const vars = {};
    for (const name of ['--background-color', '--secondary-background-color',
                        '--text-color', '--primary-color']) {
      vars[name] = cs.getPropertyValue(name).trim();
    }
    out[k] = {bg: cs.backgroundColor, color: cs.color, vars};
  }
  return out;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 1000})
    page.goto(URL, timeout=90000, wait_until="domcontentloaded")
    for _ in range(30):
        if "订单号" in page.inner_text("body"):
            break
        time.sleep(2)

    info = page.evaluate(JS)
    for k, v in info.items():
        print(k, "->", v)

    # 登录后主容器
    page.get_by_label("订单号").fill("ORDER20261021001")
    page.get_by_label("手机号后四位").fill("0001")
    page.get_by_label("手机号后四位").press("Enter")
    time.sleep(8)
    print("---- after login ----")
    info = page.evaluate(JS)
    for k, v in info.items():
        print(k, "->", v)

    head = page.evaluate("""() => {
      const el = document.querySelector('.st-key-brandhead');
      if (!el) return null;
      const cs = getComputedStyle(el);
      return {bg: cs.backgroundColor, h: el.getBoundingClientRect().height};
    }""")
    print("brandhead ->", head)
    browser.close()
