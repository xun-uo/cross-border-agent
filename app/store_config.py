# -*- coding: utf-8 -*-
"""店铺侧配置：官网跳转地址、跳转文案、客服对外名称。

存 data/store_config.json。Streamlit Cloud 免费实例的文件系统在重启后会重置，
写入会丢、回落到默认值——这是演示环境的取舍；正式版应进数据库。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "store_config.json"

DEFAULT = {
    "site_url": "",
    "site_label": "前往店铺官网",
    "agent_name": "",
}


def load():
    try:
        raw = json.loads(PATH.read_text(encoding="utf-8"))
    except Exception:
        raw = {}
    out = dict(DEFAULT)
    if isinstance(raw, dict):
        out.update({k: v for k, v in raw.items() if k in DEFAULT})
    return out


def save(cfg):
    cur = load()
    cur.update({k: v for k, v in (cfg or {}).items() if k in DEFAULT})
    PATH.write_text(json.dumps(cur, ensure_ascii=False, indent=2), encoding="utf-8")
    return cur
