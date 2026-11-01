# -*- coding: utf-8 -*-
"""查会话消息区容器的真实高度，确认 CSS 覆盖有没有生效。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"

JS = """
() => {
  const out = {};
  const el = document.querySelector('.st-key-msgbox');
  if (el) {
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    out.msgbox = {cls: el.className, inlineHeight: el.style.height,
                  computedHeight: cs.height, rectH: Math.round(r.height),
                  overflow: cs.overflowY};
  } else {
    out.msgbox = null;
    out.keys = [...document.querySelectorAll('[class*="st-key-"]')]
      .map(e => e.className).slice(0, 20);
  }
  const ci = document.querySelector('[data-testid="stChatInput"]');
  if (ci) {
    const r = ci.getBoundingClientRect();
    out.chatInput = {y: Math.round(r.y), h: Math.round(r.height),
                     pos: getComputedStyle(ci).position};
  }
  out.vh = window.innerHeight;
  out.docH = document.documentElement.scrollHeight;
  return out;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1200, "height": 1100})
    page.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(6)
    page.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    page.get_by_label("账号").fill("admin")
    page.get_by_label("密码").fill("niao2026")
    page.get_by_label("密码").press("Enter")
    time.sleep(6)
    # 会话可能落在「已回复」组里，先展开分组再点查看
    for name in ("展开", "查看"):
        try:
            page.get_by_role("button", name=name).first.click(timeout=3000)
            time.sleep(2)
        except Exception:
            pass
    print(page.evaluate(JS))
    browser.close()
