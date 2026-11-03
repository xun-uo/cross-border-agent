# -*- coding: utf-8 -*-
"""验切语言后买家消息也跟着变，且切第二次不层层失真。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"
THAI = r"[\u0e00-\u0e7f]"
VIET = r"[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]"


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


def bubbles(pg):
    return [e.inner_text() for e in pg.query_selector_all('[data-testid="stChatMessage"]')]


def switch_lang(pg, name):
    pg.locator('[data-testid="stSelectbox"]').first.click(timeout=8000)
    time.sleep(1)
    pg.get_by_text(name, exact=True).last.click(timeout=5000)
    time.sleep(14)   # 等批量翻译


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(9)

    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    time.sleep(17)

    bs = bubbles(pg)
    print("=== 中文时 %d 条 ===" % len(bs))
    for x in bs:
        print("   ", x.replace("\n", " ")[:70])

    switch_lang(pg, "ไทย")
    bs = bubbles(pg)
    print("=== 切泰语后 ===")
    for x in bs:
        print("   ", x.replace("\n", " ")[:70])
    t = body(pg)
    print("买家那句还是中文吗:", "我的订单在哪" in t)

    switch_lang(pg, "中文")
    t2 = body(pg)
    print("=== 切回中文 ===")
    print("买家那句回来了吗:", "我的订单在哪" in t2)
    for x in bubbles(pg):
        print("   ", x.replace("\n", " ")[:70])

    b.close()
