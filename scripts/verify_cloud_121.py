# -*- coding: utf-8 -*-
"""线上复核 #121：build 号、页头控件位置、待处理红点、翻译按钮。

线上 app 在 iframe 里（src 形如 //<host>/~/+/），且冷启动时 frame.url 可能是空串，
所以按「能不能读到 stApp」来认 frame。
"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CLOUD = "https://cross-border-agent.streamlit.app"
POS_JS = """() => {
  const q = s => Array.from(document.querySelectorAll(s)).map(e => {
    const r = e.getBoundingClientRect();
    return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)};
  });
  return {head: q('.shop-head-fixed'), lang: q('.st-key-lang_box, .st-key-lang_box_shop'),
          out: q('.st-key-buyer_logout, .st-key-shop_logout'), tabs: q('[role="tablist"]')};
}"""
DOT_JS = """() => {
  const b = document.querySelectorAll('[role="tablist"] [role="tab"]')[0];
  if (!b) return 'no-tab';
  const c = getComputedStyle(b, '::after').content;
  return (c && c !== 'none' && c !== 'normal') ? c : 'none';
}"""


def app_frame(pg, wait=120):
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


def wait_login(f, wait=150):
    """冷启动时 stApp 很快就有了，但登录表单还要再等十几秒。"""
    t0 = time.time()
    while time.time() - t0 < wait:
        try:
            if f.get_by_label("订单号").count():
                return True
        except Exception:
            pass
        time.sleep(3)
    return False


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)

    bp = b.new_page(viewport={"width": 1440, "height": 950})
    bp.goto(CLOUD, wait_until="domcontentloaded", timeout=120000)
    f = app_frame(bp)
    if not f:
        print("买家页没等到 app frame")
        sys.exit(1)
    if not wait_login(f):
        print("登录表单没出来，body:", f.locator("body").inner_text()[:300].replace("\n", " | "))
        sys.exit(1)
    body = f.locator("body").inner_text()
    print("build:", [ln for ln in body.split("\n") if "build" in ln][:1])

    f.get_by_label("订单号").fill("ORDER20261021001")
    f.get_by_label("手机号后四位").fill("0001")
    f.get_by_label("手机号后四位").press("Enter")
    time.sleep(14)
    b2 = app_frame(bp)
    print("买家端位置:", b2.evaluate(POS_JS))
    bp.screenshot(path="D:/跨境智服/out/cloud121_buyer.png")

    try:
        b2.locator('input[type="file"]').first.set_input_files("D:/跨境智服/out/test_upload.png")
        time.sleep(4)
        snd = b2.locator('[data-testid="stChatInput"] button[aria-label="Send message"]')
        if snd.count():
            snd.first.click()
        else:
            b2.locator('[data-testid="stChatInput"] textarea').first.press("Enter")
        time.sleep(16)
        print("买家转人工提示:", "转人工" in app_frame(bp).locator("body").inner_text())
    except Exception as e:
        print("发图失败:", e)

    mp = b.new_page(viewport={"width": 1440, "height": 950})
    mp.goto(CLOUD, wait_until="domcontentloaded", timeout=120000)
    mf = app_frame(mp)
    if not mf:
        print("商家页没等到 app frame")
        sys.exit(1)
    for _ in range(30):
        time.sleep(3)
        if mf.locator('[role="tab"]').count() >= 2:
            break
    mf.locator('[role="tab"]').nth(1).click()
    time.sleep(4)
    mf.get_by_label("账号").fill("admin")
    mf.get_by_label("密码").fill("niao2026")
    mf.get_by_label("密码").press("Enter")
    for _ in range(30):
        time.sleep(2)
        if mf.locator('[role="tablist"]').count():
            break
    time.sleep(6)
    print("商家端位置:", mf.evaluate(POS_JS))
    print("红点（打开前）:", mf.evaluate(DOT_JS))
    mp.screenshot(path="D:/跨境智服/out/cloud121_merchant.png")

    btn = mf.get_by_role("button", name="查看")
    print("查看按钮:", btn.count())
    if btn.count():
        btn.first.click()
        time.sleep(10)
        print("红点（打开后）:", mf.evaluate(DOT_JS))
        print("翻译按钮:", mf.get_by_role("button", name="翻译成中文").count())
        mp.screenshot(path="D:/跨境智服/out/cloud121_session.png")
    b.close()
