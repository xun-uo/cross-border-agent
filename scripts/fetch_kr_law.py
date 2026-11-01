# -*- coding: utf-8 -*-
"""用真实浏览器打开 law.go.kr，把《健康功能食品法》正文抓下来。"""
import io
import re
import sys
import time

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TARGETS = [
    ("건강기능식품법", "https://www.law.go.kr/법령/건강기능식품에관한법률"),
    ("식품표시광고법", "https://www.law.go.kr/법령/식품등의표시광고에관한법률"),
]

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge", headless=True)
    ctx = b.new_context(viewport={"width": 1400, "height": 1000},
                        locale="ko-KR")
    pg = ctx.new_page()
    for name, url in TARGETS:
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=90000)
            time.sleep(8)
            # 法条正文常在 iframe 或特定容器里
            txt = ""
            for sel in ("#lawcon", ".law-con", "div#content", "body"):
                try:
                    el = pg.query_selector(sel)
                    if el:
                        t = el.inner_text()
                        if len(t) > len(txt):
                            txt = t
                except Exception:
                    pass
            print("=" * 70)
            print(name, "| 抓到", len(txt), "字")
            # 找关键条文
            for kw in ("제8조", "제5조", "제6조", "부당한 표시", "질병의 예방"):
                idx = txt.find(kw)
                if idx >= 0:
                    print("\n>>> 命中 %s" % kw)
                    print(txt[max(0, idx - 120):idx + 420].replace("\n", " ")[:520])
            out = r"D:\跨境智服\out\kr_%s.txt" % name
            with open(out, "w", encoding="utf-8") as f:
                f.write(txt)
            print("\n全文已存:", out)
        except Exception as e:
            print(name, "FAIL", e)
    b.close()
