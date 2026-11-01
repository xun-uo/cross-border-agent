# -*- coding: utf-8 -*-
"""扫商家端五个 tab：逐个点开、截图、收集控制台异常与页面报错文字。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"
OUT = r"D:\跨境智服\out"
TABS = ["待处理会话", "规则库", "判定看板", "会话记录", "商品与订单", "店铺设置"]
BAD = ("Traceback", "KeyError", "TypeError", "AttributeError", "StreamlitAPIException")


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 1100})
    pg = ctx.new_page()
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)

    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    time.sleep(10)

    for i, name in enumerate(TABS):
        try:
            pg.get_by_role("tab", name=name).click(timeout=6000)
        except Exception as e:
            print("[%s] CLICK FAIL %s" % (name, e))
            continue
        time.sleep(4)
        t = body(pg)
        hits = [w for w in BAD if w in t]
        chars = len(t)
        print("[%-6s] chars=%-6d errors=%s" % (name, chars, hits or "-"))
        if chars < 200:
            print("        !! 页面几乎空白")
        pg.screenshot(path=OUT + r"\scan_tab_%d.png" % i, full_page=False)

    if errs:
        print("\n--- console errors (%d) ---" % len(errs))
        for e in errs[:15]:
            print("  ", e[:200])
    else:
        print("\nno console errors")
    b.close()
