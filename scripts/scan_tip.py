# -*- coding: utf-8 -*-
"""验物流图悬停提示的位置（应在节点上方，不遮挡节点与时间）。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 1100})
    pg = ctx.new_page()
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(9)

    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    time.sleep(18)

    nodes = pg.locator("g.rt-node")
    print("rt-node 数量 =", nodes.count())
    # 第 2、4、7 个节点各截一张，看边缘节点会不会出界
    for idx, name in ((0, "first"), (3, "mid"), (6, "last")):
        try:
            pg.locator("g.rt-node circle").nth(idx).hover(timeout=5000)
            time.sleep(1.2)
            pg.screenshot(path=r"D:\跨境智服\out\tip_%s.png" % name,
                          clip={"x": 60, "y": 180, "width": 1000, "height": 520})
            tip = pg.eval_on_selector_all(
                "g.rt-tip", "els => els.map(e => [getComputedStyle(e).opacity, e.textContent])")
            vis = [x for x in tip if x[0] != "0"]
            print("[%s] 可见提示 = %s" % (name, vis))
        except Exception as e:
            print("[%s] hover fail: %s" % (name, e))
    b.close()
