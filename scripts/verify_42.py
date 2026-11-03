# -*- coding: utf-8 -*-
"""验 #42：退出登录后再登录，聊天记录还在（按订单号复用旧 sid）。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"


def login(pg, order="ORDER20261021001", tail="0001"):
    pg.get_by_label("订单号").fill(order)
    pg.get_by_label("手机号后四位").fill(tail)
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(10)


def sid_of(pg):
    q = pg.evaluate("() => location.search")
    m = re.search(r"sid=([0-9a-zA-Z]+)", q or "")
    return m.group(1) if m else None


def wait_idle(pg, n=2):
    for _ in range(20):
        time.sleep(3)
        if pg.get_by_text("正在处理").count() == 0 and \
                pg.locator('[data-testid="stChatMessage"]').count() >= n:
            return True
    return False


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    login(pg)
    sid1 = sid_of(pg)
    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    wait_idle(pg)
    n1 = pg.locator('[data-testid="stChatMessage"]').count()
    print("第一次登录 sid:", sid1, "| 气泡:", n1)

    # 退出登录
    pg.get_by_role("button", name="退出登录").first.click()
    time.sleep(8)
    print("退出后是否回到登录页:", pg.get_by_label("订单号").count() > 0,
          "| URL:", pg.evaluate("() => location.search"))

    # 再登录
    login(pg)
    sid2 = sid_of(pg)
    wait_idle(pg, 1)
    time.sleep(4)
    n2 = pg.locator('[data-testid="stChatMessage"]').count()
    print("第二次登录 sid:", sid2, "| 气泡:", n2)
    print("sid 是否复用:", sid1 == sid2)
    print("记录是否还在:", n2 >= n1 and n2 >= 2)
    for x in pg.locator('[data-testid="stChatMessage"]').all():
        print("  气泡:", x.inner_text().replace("\n", " ")[:90])
    pg.screenshot(path="D:/跨境智服/out/relogin42.png")
    b.close()
