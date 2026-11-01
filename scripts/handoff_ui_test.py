# -*- coding: utf-8 -*-
"""本地端到端：买家说「转人工」→ 商家后台看会话 → 点查看展开。

两个独立浏览器上下文，共用同一个 streamlit 进程的内存会话表。
用法： python handoff_ui_test.py [base_url]
"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8502"
OUT = r"D:\跨境智服\out"


def body(pg):
    try:
        return pg.inner_text("body")
    except Exception:
        return ""


def login_buyer(pg):
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    for _ in range(20):
        time.sleep(1.5)
        if pg.get_by_placeholder(re.compile("输入你的问题")).count() > 0:
            return True
    return False


def login_shop(pg):
    pg.get_by_role("tab", name="商家").click()
    time.sleep(1.5)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    for _ in range(20):
        time.sleep(1.5)
        if "商家后台" in body(pg):
            return True
    return False


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)

    # --- 买家：说「转人工」 ---
    ctx_b = browser.new_context(viewport={"width": 900, "height": 1100})
    buyer = ctx_b.new_page()
    buyer.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(6)
    print("buyer login page:", "订单号" in body(buyer))
    print("buyer logged:", login_buyer(buyer))

    box = buyer.get_by_placeholder(re.compile("输入你的问题"))
    box.click()
    box.fill("转人工")
    box.press("Enter")
    print("buyer sent 转人工")
    time.sleep(6)

    # 再灌几条，把商家端的消息区撑到超过一屏，验证回复框是否还钉在底部
    for i in range(6):
        try:
            b2 = buyer.get_by_placeholder(re.compile("输入你的问题"))
            b2.click()
            b2.fill(f"补充说明第 {i + 1} 条：我的地址是浙江省杭州市西湖区某路 {100 + i} 号")
            b2.press("Enter")
            time.sleep(2.5)
        except Exception as e:
            print("  send failed:", e)
            break

    bt = body(buyer)
    print("  买家页含「已转人工」:", "转人工" in bt or "等待商家" in bt)
    buyer.screenshot(path=rf"{OUT}\handoff_buyer.png", full_page=True)

    # --- 商家：看后台 ---
    ctx_s = browser.new_context(viewport={"width": 1200, "height": 1100})
    shop = ctx_s.new_page()
    shop.goto(BASE, timeout=90000, wait_until="domcontentloaded")
    time.sleep(6)
    print("shop logged:", login_shop(shop))
    time.sleep(4)
    shop.screenshot(path=rf"{OUT}\handoff_shop_list.png", full_page=True)

    st = body(shop)
    print("商家页含会话列表:", "个进行中的人工会话" in st)

    # 点「查看」展开
    try:
        shop.get_by_role("button", name="查看").first.click(timeout=5000)
        time.sleep(5)
        shop.screenshot(path=rf"{OUT}\handoff_shop_open.png", full_page=True)
        print("expanded, shot saved")
        # 输入框应该在页面最后且钉在视口底部
        r = shop.get_by_placeholder(re.compile("以人工客服身份回复")).bounding_box()
        print("reply box y:", round(r["y"]), "height:", round(r["height"]))
        print("viewport height:", 1100)
    except Exception as e:
        print("expand failed:", e)

    # 商家回一条，看发完之后输入框会不会被顶走（用户报的就是这个）
    try:
        rb = shop.get_by_placeholder(re.compile("以人工客服身份回复"))
        rb.click()
        rb.fill("收到，我现在帮你查物流。")
        rb.press("Enter")
        time.sleep(7)
        r2 = shop.get_by_placeholder(re.compile("以人工客服身份回复")).bounding_box()
        print("after reply y:", round(r2["y"]), "(before:", round(r["y"]), ")")
        shop.screenshot(path=rf"{OUT}\handoff_shop_after.png", full_page=True)
    except Exception as e:
        print("reply failed:", e)

    browser.close()
