# -*- coding: utf-8 -*-
"""线上复核 #126：页头 AI/人工状态 + 交还 AI 后再次转人工回到「未回复」，最后清场。

线上 app 在 iframe 里，冷启动要等登录表单。
"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CLOUD = "https://cross-border-agent.streamlit.app"
DOT_JS = """() => {
  const t = document.querySelectorAll('[role="tablist"] [role="tab"]')[0];
  if (!t) return 'no-tab';
  const c = getComputedStyle(t, '::after').content;
  return (c && c !== 'none' && c !== 'normal') ? c : 'none';
}"""


def app_frame(pg, wait=150):
    t0 = time.time()
    while time.time() - t0 < wait:
        for f in pg.frames:
            if f is pg.main_frame:
                continue
            try:
                if f.locator('[data-testid="stApp"]').count():
                    return f
            except Exception:
                pass
        time.sleep(2)
    return None


def wait_login(f, wait=180):
    t0 = time.time()
    while time.time() - t0 < wait:
        try:
            if f.get_by_label("订单号").count():
                return True
        except Exception:
            pass
        time.sleep(3)
    return False


def send(f, text, tries=25):
    box = f.locator('[data-testid="stChatInput"] textarea').first
    box.fill(text)
    box.press("Enter")
    for _ in range(tries):
        time.sleep(2)
        try:
            if f.locator(".busy-pill").count() == 0 and \
                    f.get_by_text("正在处理").count() == 0:
                time.sleep(3)
                return
        except Exception:
            pass


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)

    # ---- 买家 ----
    bp = b.new_page(viewport={"width": 1440, "height": 950})
    bp.goto(CLOUD, wait_until="domcontentloaded", timeout=120000)
    f = app_frame(bp)
    if not f or not wait_login(f):
        print("买家页没就绪")
        sys.exit(1)
    txt = f.locator("body").inner_text()
    print("build:", [ln for ln in txt.split("\n") if "build" in ln][:1])

    f.get_by_label("订单号").fill("ORDER20261021008")
    f.get_by_label("手机号后四位").fill("0008")
    f.get_by_label("手机号后四位").press("Enter")
    time.sleep(14)
    f = app_frame(bp)
    print("[AI 状态] 页头:", f.locator(".shop-head-fixed").inner_text().replace("\n", " | "))

    send(f, "我要退货")
    f = app_frame(bp)
    hdr = f.locator(".shop-head-fixed").inner_text().replace("\n", " | ")
    print("[转人工后] 页头:", hdr)
    print("          橙色人工标记:", f.locator(".shop-online.is-human").count())
    bp.screenshot(path="D:/跨境智服/out/c126_buyer_human.png")

    # ---- 商家：第一次转人工应进「未回复」 ----
    mp = b.new_page(viewport={"width": 1440, "height": 950})
    mp.goto(CLOUD, wait_until="domcontentloaded", timeout=120000)
    mf = app_frame(mp)
    for _ in range(40):
        time.sleep(3)
        try:
            if mf.locator('[role="tab"]').count() >= 2:
                break
        except Exception:
            pass
    mf.locator('[role="tab"]').nth(1).click()
    time.sleep(4)
    mf.get_by_label("账号").fill("admin")
    mf.get_by_label("密码").fill("niao2026")
    mf.get_by_label("密码").press("Enter")
    for _ in range(30):
        time.sleep(2)
        try:
            if mf.locator('[role="tablist"]').count():
                break
        except Exception:
            pass
    time.sleep(6)
    body = mf.locator("body").inner_text()
    print("[商家] 未回复(1):", "未回复（1）" in body, "| 红点:", mf.evaluate(DOT_JS))

    btn = mf.get_by_role("button", name="查看")
    print("[商家] 查看按钮:", btn.count())
    if btn.count():
        btn.first.click()
        time.sleep(8)
        mf.get_by_role("button", name="结束会话（交还 AI）").first.click()
        time.sleep(10)
        print("[商家] 交还后列表空:", "暂无进行中的人工会话" in mf.locator("body").inner_text())

    # ---- 买家再触发一次人工，应回到未回复 ----
    f = app_frame(bp)
    send(f, "我要换货")
    time.sleep(10)
    mf = app_frame(mp)
    body2 = mf.locator("body").inner_text()
    print("[第二次转人工] 未回复(1):", "未回复（1）" in body2,
          "| 红点:", mf.evaluate(DOT_JS))
    print("[第二次转人工] 已回复组:", [x for x in body2.split("\n") if "已回复" in x][:1])
    mp.screenshot(path="D:/跨境智服/out/c126_merchant.png")

    # ---- 清场：把测试会话交还 AI ----
    btn2 = mf.get_by_role("button", name="查看")
    if btn2.count():
        btn2.first.click()
        time.sleep(8)
        try:
            mf.get_by_role("button", name="结束会话（交还 AI）").first.click()
            time.sleep(6)
            print("[清场] 已交还 AI:", "暂无进行中的人工会话" in mf.locator("body").inner_text())
        except Exception as e:
            print("[清场] 失败:", e)
    b.close()
