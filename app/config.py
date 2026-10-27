# -*- coding: utf-8 -*-
"""配置：从环境变量 / .env / apikey.txt 读取密钥。"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ENV_FILE = ROOT / ".env"
KEY_FILE = ROOT / "apikey.txt"

BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


def _from_streamlit_secrets(name):
    """Streamlit Cloud 上密钥放在 Secrets 里，不是环境变量。"""
    try:
        import streamlit as st
        return st.secrets.get(name)
    except Exception:
        return None


def load_api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    key = _from_streamlit_secrets("DEEPSEEK_API_KEY")
    if key:
        return str(key).strip()
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            if name.strip() == "DEEPSEEK_API_KEY":
                return value.strip().strip('"').strip("'")
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8-sig").strip()
    raise RuntimeError("找不到 API key：请设置 DEEPSEEK_API_KEY，或写入 apikey.txt / .env / Streamlit Secrets")
