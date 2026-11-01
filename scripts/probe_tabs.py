# -*- coding: utf-8 -*-
"""验证商家后台的 tabs 滚动时是否 sticky 粘在页头下面。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"

JS = """
() => {
  const out = {tabish: [], roles: []};
  document.querySelectorAll('*').forEach(e => {
    const tid = e.getAttribute('data-testid');
    const role = e.getAttribute('role');
    if (tid && /tab/i.test(tid)) out.tabish.push({tid, cls: String(e.className).slice(0,50)});
    if (role && /tab/i.test(role)) out.roles.push({role, cls: String(e.className).slice(0,50), tid: tid || ''});
  });
  out.tabish = out.tabish.slice(0, 10);
  out.roles = out.roles.slice(0, 10);
  return out;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1000, "height": 1100},
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

    print("before:", page.evaluate(JS).get("rectTop"), page.evaluate(JS).get("pos"))

    # 切到规则库（内容长），再滚动
    try:
        page.get_by_role("tab", name="规则库").click()
        time.sleep(4)
    except Exception as e:
        print("tab switch:", e)

    page.evaluate("""() => {
      const m = document.querySelector('[data-testid="stAppScrollToBottomContainer"]');
      if (m) m.scrollTop = 600;
    }""")
    time.sleep(2)
    info = page.evaluate(JS)
    print("after scroll:", info.get("rectTop"), "pos:", info.get("pos"),
          "top:", info.get("top"))
    print("chain:", info.get("chain"))
    page.screenshot(path=r"D:\跨境智服\out\probe_tabs.png")
    browser.close()
