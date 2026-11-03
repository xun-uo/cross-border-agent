# -*- coding: utf-8 -*-
"""线上（iframe 内）验证 #38：切泰语后地址栏 l=、刷新后语言是否还在。

注意：线上 app 渲染在 iframe 里（src 形如 //<host>/~/+/），必须用 frame 定位；
冷启动时 frame 的 url 可能是空字符串，所以按内容识别。
"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CLOUD = "https://cross-border-agent.streamlit.app"


def has_thai(s):
    return any("\u0e00" <= c <= "\u0e7f" for c in s)


def app_frame(pg, wait=90):
    """等 app 的 iframe 出现并能读到登录表单（冷启动可能要一分钟）。"""
    t0 = time.time()
    while time.time() - t0 < wait:
        for f in pg.frames:
            if f is pg.main_frame:
                continue
            try:
                if "订单号" in f.locator("body").inner_text():
                    return f
            except Exception:
                pass
            try:
                if f.locator('[data-testid="stApp"]').count():
                    return f
            except Exception:
                pass
        time.sleep(2)
    return None


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(CLOUD, wait_until="domcontentloaded", timeout=120000)
    f = app_frame(pg)
    if f is None:
        print("没找到 app frame，frames:", [(x.url, x.name) for x in pg.frames])
        sys.exit(1)
    txt = f.locator("body").inner_text()
    print("build 行:", [x for x in txt.split("\n") if "build" in x][:2])
    f.get_by_label("订单号").fill("ORDER20261021001")
    f.get_by_label("手机号后四位").fill("0001")
    f.get_by_label("手机号后四位").press("Enter")
    time.sleep(12)
    print("登录后 location.search:", pg.evaluate("() => location.search"))

    f = app_frame(pg)
    box = f.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的订单在哪")
    box.press("Enter")
    for _ in range(15):
        time.sleep(3)
        if f.locator('[data-testid="stChatMessage"]').count() >= 3:
            break
    print("气泡数:", f.locator('[data-testid="stChatMessage"]').count())

    f.locator('[data-testid="stSelectbox"]').first.click(timeout=10000)
    time.sleep(2)
    opt = f.locator('[role="option"]').filter(has_text="ไทย")
    print("泰语选项:", opt.count())
    opt.last.click(timeout=8000)

    seen = []
    for i in range(40):
        time.sleep(0.5)
        href = pg.evaluate("() => location.search")
        if not seen or seen[-1][1] != href:
            seen.append((round((i + 1) * 0.5, 1), href))
    print("--- 地址栏变化轨迹 ---")
    for t, h in seen:
        print(f"  {t:>5}s  {h}")
    f = app_frame(pg)
    print("界面是泰语吗:", has_thai(f.locator("body").inner_text()))
    pg.screenshot(path="D:/跨境智服/out/cloud_lang_after.png")

    pg.reload(wait_until="domcontentloaded")
    f = app_frame(pg)
    print("刷新后 location.search:", pg.evaluate("() => location.search"))
    print("刷新后界面是泰语吗:", has_thai(f.locator("body").inner_text()) if f else "no frame")
    b.close()
