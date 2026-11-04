# 一次性：逐个 tab 扫描是否还有 Streamlit 默认红 rgb(255,75,75)
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

RED_SCAN = """() => {
  const out = [];
  const walk = (el) => {
    const cs = getComputedStyle(el);
    for (const pr of ['backgroundColor','borderBottomColor','borderTopColor','color','outlineColor','borderColor']) {
      const v = cs[pr];
      if (v && v.includes('255, 75, 75')) { out.push(el.tagName + '/' + (el.getAttribute('data-testid')||'') + ' ' + pr); break; }
    }
    for (const c of el.children) walk(c);
  };
  walk(document.body);
  return [...new Set(out)];
}"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 420})
    pg.goto("http://localhost:8502", wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_role("tab", name="商家").click()
    time.sleep(2)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    time.sleep(10)

    tabs = pg.locator('[role="tablist"] [role="tab"]')
    for i in range(tabs.count()):
        tabs.nth(i).click()
        time.sleep(2)
        red = pg.evaluate(RED_SCAN)
        name = tabs.nth(i).inner_text().strip().replace("\n", " ")[:10]
        print("  [{}] {}: {}".format(i, name, red if red else "无默认红"))
    pg.screenshot(path=r"D:\跨境智服\out\tab_gold_final.png", clip={"x": 0, "y": 0, "width": 1440, "height": 200})
    b.close()
