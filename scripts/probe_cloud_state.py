# -*- coding: utf-8 -*-
"""线上现在什么状态：活着/睡着/在重新部署，build 号是多少。"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CLOUD = "https://cross-border-agent.streamlit.app"


def app_frame(pg, wait=90):
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


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(CLOUD, wait_until="domcontentloaded", timeout=120000)
    time.sleep(6)
    body = pg.locator("body").inner_text()
    print("主页面文字:", body[:200].replace("\n", " | "))
    wake = pg.get_by_role("button", name="Yes, get this app back up!")
    print("有唤醒按钮:", wake.count())
    if wake.count():
        wake.first.click()
        print("点了唤醒，等 40 秒")
        time.sleep(40)
    f = app_frame(pg)
    if not f:
        print("还是没等到 app frame；页面:", pg.locator("body").inner_text()[:200].replace("\n", " | "))
        pg.screenshot(path="D:/跨境智服/out/cloud_state.png")
        sys.exit(0)
    for _ in range(40):
        txt = f.locator("body").inner_text()
        if "build" in txt:
            break
        time.sleep(3)
    txt = f.locator("body").inner_text()
    print("build:", [ln for ln in txt.split("\n") if "build" in ln][:1])
    pg.screenshot(path="D:/跨境智服/out/cloud_state.png")
    b.close()
