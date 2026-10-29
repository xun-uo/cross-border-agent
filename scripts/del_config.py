# -*- coding: utf-8 -*-
"""删除 GitHub 仓库上的 .streamlit/config.toml（恢复 Streamlit 默认工具栏）。"""
import base64
import json
import urllib.request

TOKEN = open(r"D:\跨境智服\gh_token.txt", encoding="utf-8").read().strip()
REPO = "xun-uo/cross-border-agent"
PATH = ".streamlit/config.toml"
API = "https://api.github.com"


def req(method, url, data=None):
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header("Authorization", f"Bearer {TOKEN}")
    r.add_header("Accept", "application/vnd.github+json")
    r.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(r, timeout=40) as resp:
        return resp.status, json.loads(resp.read() or b"{}")


# 取 sha
try:
    _, info = req("GET", f"{API}/repos/{REPO}/contents/{PATH}")
    sha = info["sha"]
    print("remote file exists, sha =", sha)
except Exception as e:
    print("not found (already deleted?):", e)
    raise SystemExit(0)

status, _ = req("DELETE", f"{API}/repos/{REPO}/contents/{PATH}",
                {"message": "remove config.toml to restore default toolbar", "sha": sha,
                 "branch": "main"})
print("delete status:", status)

try:
    req("GET", f"{API}/repos/{REPO}/contents/{PATH}")
    print("STILL EXISTS")
except Exception:
    print("confirmed deleted")
