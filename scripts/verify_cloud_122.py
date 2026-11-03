# -*- coding: utf-8 -*-
"""线上复核 #122：build、时间、物流图放大、退出重登续聊、手机端并排+置顶。

线上 app 在 iframe 里（src 形如 //<host>/~/+/），冷启动时 frame.url 可能为空，
所以按「能不能读到 stApp」认 frame；登录表单还要再等十几秒。
"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CLOUD = "https://cross-border-agent.streamlit.app"
POS_JS = """() => {
  const q = s => Array.from(document.querySelectorAll(s)).map(e => {
    const r = e.getBoundingClientRect();
    const cs = getComputedStyle(e);
    return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width),
            h: Math.round(r.height), pos: cs.position};
  });
  return {head: q('.shop-head-fixed'), lang: q('.st-key-lang_box'),
          out: q('.st-key-buyer_logout')};
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


def wait_label(f, label, wait=150):
    t0 = time.time()
    while time.time() - t0 < wait:
        try:
            if f.get_by_label(label).count():
                return True
        except Exception:
            pass
        time.sleep(3)
    return False


def login(f, order, tail):
    f.get_by_label("订单号").fill(order)
    f.get_by_label("手机号后四位").fill(tail)
    f.get_by_label("手机号后四位").press("Enter")
    time.sleep(14)


def sid_of(pg):
    m = re.search(r"sid=([0-9a-zA-Z]+)", pg.evaluate("() => location.search") or "")
    return m.group(1) if m else None


def wait_idle(f, n=2, tries=20):
    for _ in range(tries):
        time.sleep(3)
        try:
            if f.get_by_text("正在处理").count() == 0 and \
                    f.locator('[data-testid="stChatMessage"]').count() >= n:
                return True
        except Exception:
            pass
    return False


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)

    # ---------- 买家桌面：build / 时间 / 物流图 ----------
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(CLOUD, wait_until="domcontentloaded", timeout=120000)
    f = app_frame(pg)
    if not f or not wait_label(f, "订单号"):
        print("登录页没等到:", pg.locator("body").inner_text()[:120])
        sys.exit(1)
    txt = f.locator("body").inner_text()
    print("build:", [ln for ln in txt.split("\n") if "build" in ln][:1])

    login(f, "ORDER20261021001", "0001")
    f = app_frame(pg)
    sid1 = sid_of(pg)
    print("登录后 sid:", sid1)
    print("桌面位置:", f.evaluate(POS_JS))

    box = f.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    wait_idle(f, 2)
    time.sleep(4)
    f = app_frame(pg)
    caps = [x for x in f.locator("body").inner_text().split("\n")
            if re.fullmatch(r"\d{2}:\d{2}", x.strip())]
    print("气泡时间:", caps[-2:] if caps else "无",
          "| 本机北京时间:", time.strftime("%H:%M"))
    print("有『现在到哪了』:", f.get_by_text("现在到哪了").count())
    print("放大按钮:", f.get_by_role("button", name="点开放大").count())
    btn = f.get_by_role("button", name="点开放大")
    if btn.count():
        btn.first.click()
        time.sleep(5)
        dlg = f.locator('[role="dialog"]')
        print("弹窗:", dlg.count(),
              "| 弹窗含『现在到哪了』:", "现在到哪了" in (dlg.first.inner_text() if dlg.count() else ""))
        pg.screenshot(path="D:/跨境智服/out/cloud122_dialog.png")
        if dlg.count():
            try:
                dlg.first.get_by_role("button").first.click()   # 关掉弹窗
            except Exception:
                pg.keyboard.press("Escape")
            time.sleep(2)

    # ---------- 退出重登续聊 ----------
    f = app_frame(pg)
    f.get_by_role("button", name="退出登录").first.click()
    time.sleep(10)
    f = app_frame(pg)
    if not wait_label(f, "订单号", 60):
        print("退出后没回到登录页")
    else:
        login(f, "ORDER20261021001", "0001")
        f = app_frame(pg)
        sid2 = sid_of(pg)
        wait_idle(f, 1)
        time.sleep(3)
        n = f.locator('[data-testid="stChatMessage"]').count()
        print("重登 sid:", sid2, "| 是否复用:", sid1 == sid2, "| 气泡数:", n)

    # ---------- 手机 390：并排 + 置顶 ----------
    mp = b.new_page(viewport={"width": 390, "height": 844})
    mp.goto(CLOUD + "/?o=ORDER20261021003&r=buyer&sid=x", wait_until="domcontentloaded",
            timeout=120000)
    time.sleep(10)
    mp.goto(CLOUD, wait_until="domcontentloaded", timeout=120000)
    mf = app_frame(mp)
    if mf and wait_label(mf, "订单号", 120):
        login(mf, "ORDER20261021003", "0003")
        mf = app_frame(mp)
        print("手机位置:", mf.evaluate(POS_JS))
        mp.screenshot(path="D:/跨境智服/out/cloud122_mobile.png")
        # 滚动后页头还在不在
        mf.evaluate("() => window.scrollTo(0, 400)")
        time.sleep(2)
        print("滚动后页头 y:", mf.evaluate(
            "() => { const e = document.querySelector('.shop-head-fixed');"
            " return e ? Math.round(e.getBoundingClientRect().y) : null; }"))
    else:
        print("手机端没进到聊天页")
    b.close()
