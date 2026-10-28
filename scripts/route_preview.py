# -*- coding: utf-8 -*-
"""物流路线示意图 v2：深色卡片 + 时间轴，描述交给下方列表。"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"D:\跨境智服\out\route_preview.png")
BG = (24, 34, 50, 255)
LINE = (70, 110, 160, 255)
DOT = (66, 133, 244, 255)
DOT_NOW = (56, 200, 120, 255)
TXT_DIM = (140, 155, 175, 255)
TXT = (225, 232, 245, 255)


def load_font(size):
    for p in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def route_image(nodes, order_no="", width=1000, height=150):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, width - 1, height - 1], radius=14, fill=BG)

    f_title = load_font(15)
    f_small = load_font(12)
    f_big = load_font(14)

    d.text((24, 14), f"Route · {order_no}" if order_no else "Route", font=f_title, fill=TXT)

    n = len(nodes)
    x0, x1 = 74, width - 74
    y = 86
    step = (x1 - x0) / (n - 1) if n > 1 else 0

    d.line([(x0, y), (x1, y)], fill=LINE, width=3)

    for i, node in enumerate(nodes):
        x = x0 + step * i
        last = i == n - 1
        if last:
            d.ellipse([x - 17, y - 17, x + 17, y + 17], outline=(56, 200, 120, 110), width=2)
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=DOT_NOW)
        else:
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=DOT)

        # 序号在点的上方
        d.text((x, y - 30), str(i + 1), font=f_small, fill=TXT_DIM, anchor="ma")
        # 时间在点的下方
        t = node["time"][5:16] if len(node["time"]) >= 16 else node["time"]
        d.text((x, y + 18), t, font=f_small,
               fill=DOT_NOW if last else TXT_DIM, anchor="ma")

    d.text((x0, y + 40), "ORIGIN", font=f_big, fill=TXT_DIM, anchor="ma")
    d.text((x1, y + 40), "NOW", font=f_big, fill=DOT_NOW, anchor="ma")
    return img


if __name__ == "__main__":
    orders = json.loads(Path(r"D:\跨境智服\data\orders.json").read_text(encoding="utf-8"))
    order = next(o for o in orders if o["order_no"] == "ORDER20261021001")
    img = route_image(order["nodes"], order["order_no"])
    img.save(OUT)
    print("saved", OUT, img.size)
