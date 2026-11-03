# -*- coding: utf-8 -*-
"""统一时间：气泡和日志都按**北京时间**显示。

为什么不用 `ZoneInfo("Asia/Shanghai")`：线上跑在 Streamlit Cloud 容器里，
不保证装了 tzdata，拿不到时区会抛 ZoneInfoNotFoundError。东八区没有夏令时，
用固定偏移最稳，也不会因为容器时钟的 TZ 环境变量变成 UTC。

踩过的坑（#44）：原来三处 `_now()` 各写各的 `datetime.now()` / `time.strftime()`，
本地 Windows 是北京时间，看不出问题；一上线容器是 UTC，气泡时间整整慢 8 小时。
"""
import datetime

TZ = datetime.timezone(datetime.timedelta(hours=8))


def now_local():
    """现在（北京时间，带时区）。"""
    return datetime.datetime.now(TZ)


def hhmm():
    """气泡上的时间：HH:MM。"""
    return now_local().strftime("%H:%M")


def full():
    """日志 / 会话记录用的时间：YYYY-MM-DD HH:MM:SS。"""
    return now_local().strftime("%Y-%m-%d %H:%M:%S")
