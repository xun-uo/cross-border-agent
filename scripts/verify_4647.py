# -*- coding: utf-8 -*-
"""验 #46①（处理中固定小条）和 #47（交还 AI 后再次转人工回到「未回复」）。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"


def buyer_login(pg):
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021003")
    pg.get_by_label("手机号后四位").fill("0003")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(10)


def merchant_login(pg):
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.locator('[role="tab"]').nth(1).click()
    time.sleep(3)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    for _ in range(20):
        time.sleep(2)
        if pg.locator('[role="tablist"]').count():
            return True
    return False


def send(pg, text):
    box = pg.locator('[data-testid="stChatInput"] textarea').first
    box.fill(text)
    box.press("Enter")
    return time.time()


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    bp = b.new_page(viewport={"width": 1440, "height": 950})
    buyer_login(bp)

    # ---- #46① 处理中固定小条 ----
    t0 = send(bp, "我的订单在哪")
    seen, top = 0, None
    for i in range(30):
        time.sleep(0.4)
        try:
            n = bp.locator(".busy-pill").count()
        except Exception:
            n = 0
        if n and not seen:
            box = bp.locator(".busy-pill").first.bounding_box()
            top = box
            bp.screenshot(path="D:/跨境智服/out/busy_pill.png")
        seen = max(seen, n)
        if i > 6 and n == 0 and bp.locator('[data-testid="stChatMessage"]').count() >= 3:
            break
    print("处理中小条出现次数:", seen, "| 位置:", top)

    # ---- #47：第一次转人工 → 交还 AI → 第二次转人工 ----
    send(bp, "我要退货")
    time.sleep(18)
    print("买家气泡数:", bp.locator('[data-testid="stChatMessage"]').count())

    mp = b.new_page(viewport={"width": 1440, "height": 950})
    merchant_login(mp)
    time.sleep(6)
    body = mp.locator("body").inner_text()
    print("第一次转人工 → 未回复组:", "未回复（1）" in body or "未回复 (1)" in body)

    # 商家：结束会话（交还 AI）
    mp.get_by_role("button", name="查看").first.click()
    time.sleep(6)
    mp.get_by_role("button", name="结束会话（交还 AI）").first.click()
    time.sleep(8)
    print("交还后 body 含未回复(0):", "未回复（0）" in mp.locator("body").inner_text())

    # 买家再触发一次人工
    send(bp, "我要换货")
    time.sleep(20)
    time.sleep(8)   # 等商家端 6 秒轮询刷新
    body2 = mp.locator("body").inner_text()
    print("第二次转人工 → 商家未回复组:", "未回复（1）" in body2 or "未回复 (1)" in body2)
    print("已回复组:", [ln for ln in body2.split("\n") if "已回复" in ln][:2])
    mp.screenshot(path="D:/跨境智服/out/status47.png")
    b.close()
