# -*- coding: utf-8 -*-
"""查页头 sticky 为什么没生效：看 position 计算值、滚动祖先链、滚动后的实际位置。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"

INFO = """
() => {
  const el = document.querySelector('.shop-head-fixed');
  if (!el) return {err: 'no .shop-head-fixed'};
  const cs = getComputedStyle(el);
  const r = el.getBoundingClientRect();
  const chain = [];
  let p = el.parentElement;
  while (p && chain.length < 7) {
    const s = getComputedStyle(p);
    chain.push({
      tag: p.tagName.toLowerCase(),
      testid: p.getAttribute('data-testid') || '',
      overflow: s.overflowY,
      pos: s.position,
      h: Math.round(p.getBoundingClientRect().height),
      scrollable: p.scrollHeight > p.clientHeight + 2,
      st: Math.round(p.getBoundingClientRect().top),
    });
    p = p.parentElement;
  }
  return {
    position: cs.position, top: cs.top, zIndex: cs.zIndex,
    rectTop: Math.round(r.top), rectH: Math.round(r.height),
    winScrollY: window.scrollY, chain,
  };
}
"""


def find_scroller(page):
    return page.evaluate("""() => {
      const cands = ['[data-testid="stMain"]', '[data-testid="stAppViewContainer"]',
                     'section.stMain', 'body', 'html'];
      const out = [];
      for (const c of cands) {
        const el = document.querySelector(c);
        if (!el) continue;
        out.push({sel: c, sh: el.scrollHeight, ch: el.clientHeight,
                  oy: getComputedStyle(el).overflowY});
      }
      return out;
    }""")


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    page.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(6)
    page.get_by_label("订单号").fill("ORDER20261021001")
    page.get_by_label("手机号后四位").fill("0001")
    page.get_by_label("手机号后四位").press("Enter")
    time.sleep(7)

    # 灌几条消息把页面撑长
    for i in range(4):
        try:
            box = page.get_by_placeholder(re.compile("输入你的问题"))
            box.click()
            box.fill(f"第 {i+1} 条测试消息，用来把页面撑长一点")
            box.press("Enter")
            time.sleep(4)
        except Exception as e:
            print("send fail:", e)
            break

    print("== before scroll ==")
    print(page.evaluate(INFO))

    # 试着滚各种容器
    page.evaluate("""() => {
      for (const c of ['[data-testid="stMain"]', '[data-testid="stAppScrollToBottomContainer"]',
                       '[data-testid="stAppViewContainer"]']) {
        const el = document.querySelector(c);
        if (el) el.scrollTop = 500;
      }
      window.scrollTo(0, 500);
    }""")
    time.sleep(2)

    print("== after scroll ==")
    print(page.evaluate(INFO))
    page.screenshot(path=r"D:\跨境智服\out\probe_sticky.png")
    print("shot: probe_sticky.png")
    browser.close()
