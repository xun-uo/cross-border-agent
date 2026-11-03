# -*- coding: utf-8 -*-
"""商家页：页头下面那 96px 是哪来的（含 h=0 的子元素和 margin/gap）。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

JS = """() => {
  const root = document.querySelector('[data-testid="stMainBlockContainer"]');
  const block = root.firstElementChild;
  const cs = getComputedStyle(block);
  const out = {block: {y: Math.round(block.getBoundingClientRect().y),
                       h: Math.round(block.getBoundingClientRect().height),
                       gap: cs.gap, padTop: cs.paddingTop, disp: cs.display}};
  out.children = Array.from(block.children).map(c => {
    const r = c.getBoundingClientRect();
    const s = getComputedStyle(c);
    return {tag: c.tagName.toLowerCase(), tid: c.getAttribute('data-testid') || '',
            cls: (c.className||'').toString().slice(0,40),
            y: Math.round(r.y), h: Math.round(r.height),
            mt: s.marginTop, mb: s.marginBottom, pos: s.position,
            txt: (c.innerText||'').replace(/\\n/g,' ').slice(0,24)};
  });
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto("http://localhost:8502", wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg.get_by_text("商家", exact=True).first.click()
    time.sleep(3)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    time.sleep(11)
    info = pg.evaluate(JS)
    print("block:", info["block"])
    for c in info["children"]:
        print(f"  y={c['y']:>4} h={c['h']:>4} pos={c['pos']:<9} mt={c['mt']:<6} mb={c['mb']:<6} "
              f"{c['tag']:<8} {c['tid']:<22} {c['txt']!r}")
    b.close()
