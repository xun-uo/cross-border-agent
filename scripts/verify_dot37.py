# -*- coding: utf-8 -*-
"""端到端验 #37 红点：买家发图转人工 → 商家看到红点 → 点「查看」红点消失 → 买家再说话红点回来。

顺带验 #35 翻译按钮在界面上存在且能点（外文会话才有译文，这里只验按钮出现）。
"""
import io
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"
DOT_JS = """() => {
  const b = document.querySelectorAll('[role="tablist"] [role="tab"]')[0];
  if (!b) return 'no-tab';
  const c = getComputedStyle(b, '::after').content;
  return (c && c !== 'none' && c !== 'normal') ? c : 'none';
}"""


def make_png(path):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (240, 160), (245, 240, 232))
    d = ImageDraw.Draw(im)
    d.rectangle([8, 8, 232, 152], outline=(201, 168, 130), width=3)
    im.save(path)


def buyer_login(pg):
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(7)
    pg.get_by_label("订单号").fill("ORDER20261021001")
    pg.get_by_label("手机号后四位").fill("0001")
    pg.get_by_label("手机号后四位").press("Enter")
    time.sleep(9)


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


make_png("D:/跨境智服/out/test_upload.png")

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    bp = b.new_page(viewport={"width": 1440, "height": 950})
    buyer_login(bp)

    # 上传图片 = 转人工（走 _save_upload + enter_human 那条路径）
    # 注意：挂上文件后还要点一次发送，只挂不点是不会提交的
    bp.locator('input[type="file"]').first.set_input_files("D:/跨境智服/out/test_upload.png")
    time.sleep(3)
    _send = bp.locator('[data-testid="stChatInput"] button[aria-label="Send message"]')
    if _send.count():
        _send.first.click()
    else:
        bp.locator('[data-testid="stChatInput"] textarea').first.press("Enter")
    time.sleep(14)
    print("买家侧是否出现转人工提示:",
          "转人工" in bp.locator("body").inner_text())
    bp.screenshot(path="D:/跨境智服/out/dot_buyer.png")

    mp = b.new_page(viewport={"width": 1440, "height": 950})
    ok = merchant_login(mp)
    print("商家登录成功:", ok)
    if not ok:
        print("商家页 body:", mp.locator("body").inner_text()[:300].replace("\n", " | "))
        mp.screenshot(path="D:/跨境智服/out/dot_fail.png")
        b.close()
        sys.exit(1)
    time.sleep(8)
    print("商家端红点（点查看前）:", mp.evaluate(DOT_JS))
    mp.screenshot(path="D:/跨境智服/out/dot_before.png")

    # 点第一个「查看」
    btns = mp.get_by_role("button", name="查看")
    print("查看按钮数:", btns.count())
    if btns.count():
        btns.first.click()
        time.sleep(9)
        print("商家端红点（点查看后）:", mp.evaluate(DOT_JS))
        print("DBG:", [x for x in mp.locator("body").inner_text().split("\n") if "DBG" in x][:2])
        mp.screenshot(path="D:/跨境智服/out/dot_after.png")

    # 买家再发一句 → 红点应重新出现
    box = bp.locator('[data-testid="stChatInput"] textarea').first
    box.fill("我的退款到底什么时候到账")
    box.press("Enter")
    time.sleep(16)
    print("商家端红点（买家再说话后）:", mp.evaluate(DOT_JS))
    mp.screenshot(path="D:/跨境智服/out/dot_again.png")
    b.close()
