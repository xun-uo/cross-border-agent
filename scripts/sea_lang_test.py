# -*- coding: utf-8 -*-
"""验证东南亚语种：界面切换 + 用该语言提问后端是否用同语言回复。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"
OUT = r"D:\跨境智服\out"

CASES = [
    ("Tiếng Việt", "Đơn hàng của tôi đang ở đâu?", "vi"),
    ("ไทย", "คำสั่งซื้อของฉันอยู่ไหน?", "th"),
    ("Bahasa", "Di mana pesanan saya?", "id"),
]


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


def pick_language(pg, name):
    sb = pg.get_by_role("combobox").first
    sb.click()
    time.sleep(1)
    pg.get_by_role("option", name=name, exact=True).click()
    time.sleep(4)


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    for label, question, code in CASES:
        ctx = browser.new_context(viewport={"width": 1100, "height": 1000},
                                  color_scheme="dark")
        pg = ctx.new_page()
        pg.goto(BASE, timeout=90000, wait_until="domcontentloaded")
        time.sleep(6)
        try:
            pick_language(pg, label)
        except Exception as e:
            print(f"[{code}] 切语言失败: {e}")
            ctx.close()
            continue
        t = body(pg)
        print(f"[{code}] 登录页已切换:", question[:0] or ("Đăng nhập" in t or "เข้าสู่ระบบ" in t
                                                       or "Masuk" in t))
        pg.get_by_label(re.compile("Mã đơn hàng|หมายเลขคำสั่งซื้อ|Nomor pesanan")).fill(
            "ORDER20261021001")
        pg.get_by_label(re.compile("4 số cuối|เลขท้าย|digit terakhir")).fill("0001")
        pg.get_by_label(re.compile("4 số cuối|เลขท้าย|digit terakhir")).press("Enter")
        time.sleep(8)
        box = pg.get_by_placeholder(re.compile("Nhập câu hỏi|พิมพ์คำถาม|Tulis pertanyaan"))
        box.fill(question)
        box.press("Enter")
        time.sleep(12)
        t2 = body(pg)
        # 粗略判断回复语种：看有没有该语言的常见特征
        feat = {"vi": ["đơn", "của", "hàng", "Đơn"],
                "th": ["คำสั่งซื้อ", "ของ", "ค่ะ", "คะ"],
                "id": ["pesanan", "Anda", "kami"]}[code]
        hit = sum(1 for f in feat if f in t2)
        print(f"[{code}] 提问后页面出现该语言特征词 {hit}/{len(feat)}")
        pg.screenshot(path=rf"{OUT}\sea_{code}.png", full_page=True)
        ctx.close()
    browser.close()
