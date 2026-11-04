# 一次性：验证 ⋮ 菜单里的 深色/浅色 切换对整页是否可用（登录后的聊天页）
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"
OUT = r"D:\跨境智服\out"


def bg(pg):
    return pg.evaluate(
        """() => {
        const app = document.querySelector('[data-testid="stApp"]');
        const cs = getComputedStyle(app);
        const body = getComputedStyle(document.body);
        return { appBg: cs.backgroundColor, appColor: cs.color, bodyBg: body.backgroundColor };
    }"""
    )


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 950})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_label("订单号").fill("ORDER20261021011")
    pg.get_by_label("手机号后四位").fill("0011")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(8)
    pg.screenshot(path=rf"{OUT}\theme_light_chat.png")
    print("浅色 聊天页:", bg(pg))
    print("页头文案:", [ln for ln in pg.locator("body").inner_text().split("\n") if "在线" in ln][:1])

    # 打开 ⋮ -> 点 Dark
    pg.click('[data-testid="stMainMenuButton"]')
    time.sleep(1)
    dark = pg.query_selector('button:has-text("Dark")')
    print("找到 Dark 按钮:", bool(dark))
    if dark:
        dark.click()
        time.sleep(3)
        pg.screenshot(path=rf"{OUT}\theme_dark_chat.png")
        print("深色 聊天页:", bg(pg))

    # 再切回 System
    pg.click('[data-testid="stMainMenuButton"]')
    time.sleep(1)
    sysb = pg.query_selector('button:has-text("System")')
    if sysb:
        sysb.click()
        time.sleep(3)
        print("切回 System:", bg(pg))
    b.close()
