# 一次性：验证规则库表格新列与「保存修改」不丢数据
import io
import json
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "http://localhost:8502"
OUT = r"D:\跨境智服\out"


def rule_count():
    return len(json.load(open(r"D:\跨境智服\data\rules_runtime.json", encoding="utf-8")))


with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(URL, wait_until="domcontentloaded", timeout=90000)
    time.sleep(8)
    pg.get_by_role("tab", name="商家").click()
    time.sleep(2)
    pg.get_by_label("账号").fill("admin")
    pg.get_by_label("密码").fill("niao2026")
    pg.get_by_label("密码").press("Enter")
    time.sleep(10)

    # 进「规则库」
    pg.get_by_role("tab", name="规则库").click()
    time.sleep(4)

    body = pg.locator("body").inner_text()
    print("规则总数指标:", [ln for ln in body.split("\n") if "规则总数" in ln or "已核对条款" in ln][:3])
    print("表格列名是否含触发词:", "触发词（中文）" in body, "触发词（英文）" in body)
    print("表格列名是否含豁免情形:", "豁免情形" in body)
    print("说明文案:", [ln for ln in body.split("\n") if "表格底部新增" in ln][:1])
    print("保存前规则数:", rule_count())
    pg.screenshot(path=rf"{OUT}\rules_editor_new.png", full_page=False)

    # 点当前可见的「保存修改」
    btn = pg.locator('[data-testid="stBaseButton-primary"]:visible').first
    print("保存按钮文本:", btn.inner_text().strip())
    btn.click()
    time.sleep(6)
    body2 = pg.locator("body").inner_text()
    print("保存后提示:", [ln for ln in body2.split("\n") if "已保存" in ln or "校验未通过" in ln][:2])
    print("保存后规则数:", rule_count())
    b.close()
