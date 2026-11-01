# -*- coding: utf-8 -*-
"""实验：直接用 JS 改消息区高度，看 Streamlit 的行内样式能不能被压掉。

只诊断，不改代码。用完即弃。
"""
import io
import json
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"

READ = """
() => {
  const el = document.querySelector('.st-key-msgbox');
  if (!el) return {err: 'no msgbox'};
  const r = el.getBoundingClientRect();
  return {
    inlineHeight: el.style.height,
    inlineCSS: el.getAttribute('style'),
    computed: getComputedStyle(el).height,
    rectH: Math.round(r.height),
    overflow: getComputedStyle(el).overflowY,
    hasScroll: el.scrollHeight > el.clientHeight + 2,
    childHTML: el.children.length,
  };
}
"""

SET = """
(h) => {
  const el = document.querySelector('.st-key-msgbox');
  if (!el) return 'no el';
  el.style.setProperty('height', h + 'px', 'important');
  return el.style.height;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1000, "height": 1000})
    page = ctx.new_page()
    page.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(6)
    page.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    page.get_by_label("账号").fill("admin")
    page.get_by_label("密码").fill("niao2026")
    page.get_by_label("密码").press("Enter")
    time.sleep(7)
    # 会话可能落在「已回复」分组里，先展开分组再点查看
    for name in ("展开", "查看"):
        try:
            page.get_by_role("button", name=name).first.click(timeout=3000)
            time.sleep(2)
        except Exception:
            pass

    print("BEFORE:", json.dumps(page.evaluate(READ), ensure_ascii=False))
    print("SET ->", page.evaluate(SET, 700))
    time.sleep(1)
    print("AFTER :", json.dumps(page.evaluate(READ), ensure_ascii=False))
    page.screenshot(path=r"D:\跨境智服\out\probe_height.png", full_page=True)
    browser.close()
