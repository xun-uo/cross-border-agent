# -*- coding: utf-8 -*-
"""打开线上演示站，确认部署版本与登录页是否可用。

只读，不改任何东西。用于「录视频前确认线上是新版」。
"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "https://cross-border-agent.streamlit.app"
SHOT = r"D:\跨境智服\out\online_check.png"
BUILD_RE = re.compile(r"#\d+\s*·[^\n]*")


def wait_ready(page, budget=150):
    """等 Streamlit Cloud 唤醒并渲染出正文。返回整个 body 文本。"""
    start = time.time()
    clicked = False
    while time.time() - start < budget:
        try:
            text = page.inner_text("body")
        except Exception:
            text = ""
        if "跨境智服" in text or "订单号" in text or "商家" in text:
            return text
        if not clicked:
            for label in ("get this app back up", "Yes, get this app back up",
                          "Wake up", "wake it up"):
                try:
                    page.get_by_text(label, exact=False).first.click(timeout=1500)
                    clicked = True
                    print(f"[wake] clicked: {label}")
                    break
                except Exception:
                    continue
        time.sleep(3)
    return text


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1200})
    page.goto(URL, timeout=120000, wait_until="domcontentloaded")
    body = wait_ready(page)

    m = BUILD_RE.search(body)
    print("BUILD:", m.group(0).strip() if m else "NOT FOUND（可能仍在唤醒或已休眠）")

    for kw in ("买家", "商家", "订单号", "手机", "密码"):
        print(f"  has {kw}: {kw in body}")

    page.screenshot(path=SHOT, full_page=True)
    print("screenshot:", SHOT)
    print("---- body 前 500 字 ----")
    print(body[:500])
    browser.close()
