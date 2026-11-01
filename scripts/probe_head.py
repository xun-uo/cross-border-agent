# -*- coding: utf-8 -*-
"""查 .shop-head-fixed 到底渲染成什么样。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"

CHECK = """
() => {
  const el = document.querySelector('.shop-head-fixed');
  if (!el) {
    const anyHead = [...document.querySelectorAll('[class*="shop-"]')]
      .map(e => e.className);
    return {err: 'no .shop-head-fixed', found: anyHead.slice(0, 10)};
  }
  const r = el.getBoundingClientRect();
  const cs = getComputedStyle(el);
  const kids = [...el.querySelectorAll('*')].slice(0, 8).map(e => {
    const rr = e.getBoundingClientRect();
    const s = getComputedStyle(e);
    return {tag: e.tagName, cls: String(e.className).slice(0, 30),
            w: Math.round(rr.width), h: Math.round(rr.height),
            top: Math.round(rr.top), left: Math.round(rr.left),
            color: s.color, display: s.display, vis: s.visibility};
  });
  return {
    rect: {t: Math.round(r.top), l: Math.round(r.left),
           w: Math.round(r.width), h: Math.round(r.height)},
    pos: cs.position, z: cs.zIndex, bg: cs.backgroundColor,
    display: cs.display, vis: cs.visibility, op: cs.opacity,
    overflow: cs.overflow,
    text: (el.innerText || '').slice(0, 80),
    kids,
  };
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(6)
    page.get_by_label("订单号").fill("ORDER20261021001")
    page.get_by_label("手机号后四位").fill("0001")
    page.get_by_label("手机号后四位").press("Enter")
    time.sleep(8)
    import json
    print(json.dumps(page.evaluate(CHECK), ensure_ascii=False, indent=2))
    page.screenshot(path=r"D:\跨境智服\out\probe_head.png")
    browser.close()
