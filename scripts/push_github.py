# -*- coding: utf-8 -*-
"""用 GitHub API 上传项目文件（机器上没有 git，走 Contents API）。

只上传源码与数据，排除 .venv / out / __pycache__ / 密钥文件。
"""
import base64
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

OWNER, REPO = "xun-uo", "cross-border-agent"
ROOT = Path(r"D:\跨境智服")
TOKEN = (ROOT / "gh_token.txt").read_text(encoding="utf-8").strip()

SKIP_DIRS = {".venv", "__pycache__", ".git", "out"}
SKIP_FILES = {"apikey.txt", "gh_token.txt", ".env", "_usage.json"}
INCLUDE_EXT = {".py", ".json", ".md", ".ps1", ".cmd", ".txt", ".yml", ".yaml", ".toml", ".cfg", ".ini"}

API = "https://api.github.com"


def call(method, path, body=None, expect=(200, 201, 204)):
    url = f"{API}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", "replace")
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        return e.code, {"error": detail}


def ensure_repo():
    st, data = call("GET", f"/repos/{OWNER}/{REPO}")
    if st == 200:
        print(f"repo exists: {data.get('full_name')} default_branch={data.get('default_branch')}")
        return True
    if st == 404:
        st2, d2 = call("POST", "/user/repos", {
            "name": REPO,
            "description": "Cross-border customer-service agent with compliance self-check",
            "private": False,
            "auto_init": False,
        })
        if st2 in (200, 201):
            print(f"repo created: {d2.get('full_name')}")
            time.sleep(2)
            return True
        print(f"create failed: {st2} {d2}")
        return False
    print(f"repo check failed: {st} {data}")
    return False


def collect():
    out = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        parts = set(rel.parts)
        if parts & SKIP_DIRS:
            continue
        if rel.name in SKIP_FILES:
            continue
        if p.suffix.lower() not in INCLUDE_EXT:
            continue
        out.append((rel.as_posix(), p))
    return sorted(out)


def existing_sha(path_in_repo):
    st, data = call("GET", f"/repos/{OWNER}/{REPO}/contents/{urllib.parse.quote(path_in_repo)}")
    if st == 200 and isinstance(data, dict):
        return data.get("sha")
    return None


def upload(path_in_repo, file_path):
    content = file_path.read_bytes()
    body = {
        "message": f"add {path_in_repo}",
        "content": base64.b64encode(content).decode("ascii"),
        "branch": "main",
    }
    sha = existing_sha(path_in_repo)
    if sha:
        body["sha"] = sha
        body["message"] = f"update {path_in_repo}"
    st, data = call("PUT", f"/repos/{OWNER}/{REPO}/contents/{urllib.parse.quote(path_in_repo)}", body)
    return st, data


def main():
    if not ensure_repo():
        return 1
    files = collect()
    print(f"files to upload: {len(files)}")
    ok = fail = 0
    for rel, full in files:
        st, data = upload(rel, full)
        if st in (200, 201):
            ok += 1
            print(f"  OK   {rel}")
        else:
            fail += 1
            print(f"  FAIL {rel}: {st} {str(data)[:200]}")
    print(f"\nuploaded={ok} failed={fail}")
    st, data = call("GET", f"/repos/{OWNER}/{REPO}")
    if st == 200:
        print(f"repo url: {data.get('html_url')}  size={data.get('size')}KB")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
