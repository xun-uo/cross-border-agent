# -*- coding: utf-8 -*-
"""红点被裁掉了：查 tab 及祖先的 overflow，找到裁剪者。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

JS = """() => {
  const tab = document.querySelectorAll('[role="tablist"] [role="tab"]')[0];
  const out = [];
  let el = tab;
  while (el && el !== document.documentElement) {
    const s = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    out.push({tag: el.tagName, tid: el.getAttribute('data-testid') || '',
              cls: (el.className||'').toString().slice(0,28),
              ov: s.overflow, ovx: s.overflowX, ovy: s.overflowY,
              y: Math.round(r.y), h: Math.round(r.height), pos: s.position});
    el = el.parentElement;
  }
  const t = tab.getBoundingClientRect();
  const a = getComputedStyle(tab, '::after');
  return {chain: out, tabRect: {x: Math.round(t.x), y: Math.round(t.y), w: Math.round(t.width), h: Math.round(t.height)},
          after: {top: a.top, right: a.right, pos: a.position, w: a.width, h: a.height}};
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto("http://localhost:8502", wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.locator('[role="tab"]').nth(1).click()
    time.sleep(3)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    for _ in range(20):
        time.sleep(2)
        if pg.locator('[role="tablist"]').count():
            break
    time.sleep(6)
    info = pg.evaluate(JS)
    print("tabRect:", info["tabRect"])
    print("after:", info["after"])
    for c in info["chain"]:
        print(f"  y={c['y']:>4} h={c['h']:>4} pos={c['pos']:<9} ov={c['ov']:<12} "
              f"{c['tag']:<8} {c['tid']:<16} {c['cls']}")
    b.close()
