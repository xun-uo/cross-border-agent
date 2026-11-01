# -*- coding: utf-8 -*-
"""查明 Streamlit 1.66 里 tabs 那个横条的 DOM 标识，并验证滚动后是否 sticky。"""
import io
import json
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"

DUMP = """
() => {
  const out = {tabish: [], roles: []};
  document.querySelectorAll('*').forEach(e => {
    const tid = e.getAttribute('data-testid');
    const role = e.getAttribute('role');
    if (tid && /tab/i.test(tid)) out.tabish.push({tid: tid, cls: String(e.className).slice(0,60)});
    if (role && /tab/i.test(role)) out.roles.push({role: role, tid: tid || '', cls: String(e.className).slice(0,60)});
  });
  out.tabish = out.tabish.slice(0, 8);
  out.roles = out.roles.slice(0, 8);
  const tl = document.querySelector('[role="tablist"]');
  if (tl) {
    const cs = getComputedStyle(tl);
    const r = tl.getBoundingClientRect();
    out.tablist = {pos: cs.position, top: cs.top, z: cs.zIndex,
                   rectTop: Math.round(r.top), rectH: Math.round(r.height),
                   parentOverflow: getComputedStyle(tl.parentElement).overflowY,
                   parentH: Math.round(tl.parentElement.getBoundingClientRect().height)};
  } else {
    out.tablist = null;
  }
  return out;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1000, "height": 1000},
                              color_scheme="dark")
    page = ctx.new_page()
    page.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(6)
    page.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    page.get_by_label("账号").fill("admin")
    page.get_by_label("密码").fill("niao2026")
    page.get_by_label("密码").press("Enter")
    time.sleep(8)

    try:
        page.get_by_role("tab", name="规则库").click()
        time.sleep(5)
    except Exception as e:
        print("tab switch:", e)

    print("BEFORE:", json.dumps(page.evaluate(DUMP), ensure_ascii=False))

    page.evaluate("""() => {
      const m = document.querySelector('[data-testid="stAppScrollToBottomContainer"]');
      if (m) m.scrollTop = 99999;
    }""")
    time.sleep(2)
    print("AFTER :", json.dumps(page.evaluate(DUMP), ensure_ascii=False))
    page.screenshot(path=r"D:\跨境智服\out\probe_tabs.png")
    browser.close()
