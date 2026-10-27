# -*- coding: utf-8 -*-
"""DeepSeek 客户端（仅依赖标准库）。"""
import json
import time
import urllib.error
import urllib.request

from .config import BASE_URL, MODEL, load_api_key


class LLMError(RuntimeError):
    pass


_last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}


def usage_snapshot():
    return dict(_last_usage)


def chat(messages, *, json_mode=False, temperature=0.0, max_tokens=800,
         timeout=60, retries=2):
    """调用 DeepSeek，返回文本。json_mode 时强制 JSON 对象输出。"""
    key = load_api_key()
    body = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last_err = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(
            f"{BASE_URL}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            choice = data["choices"][0]["message"]["content"]
            usage = data.get("usage") or {}
            _last_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
            _last_usage["completion_tokens"] += usage.get("completion_tokens", 0)
            _last_usage["calls"] += 1
            return choice
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            last_err = LLMError(f"HTTP {e.code}: {detail}")
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(1.5 * (attempt + 1))
                continue
            raise last_err
        except Exception as e:  # 网络类
            last_err = LLMError(f"{type(e).__name__}: {e}")
            time.sleep(1.0 * (attempt + 1))
    raise last_err


def warmup():
    """预热：提前打通连接，避免演示时第一条消息吃冷启动。"""
    try:
        chat([{"role": "user", "content": "hi"}], max_tokens=4, timeout=20, retries=1)
        return True
    except Exception:
        return False


def chat_json(messages, **kw):
    """要求返回 JSON，解析失败时重试一次。"""
    text = chat(messages, json_mode=True, **kw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        retry = messages + [
            {"role": "assistant", "content": text},
            {"role": "user", "content": "上一条不是合法 JSON。请只输出 JSON 对象，不要任何解释。"},
        ]
        text2 = chat(retry, json_mode=True, **kw)
        return json.loads(text2)
