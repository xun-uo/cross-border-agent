# -*- coding: utf-8 -*-
"""DeepSeek 客户端（仅依赖标准库）。"""
import json
import queue
import threading
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
         timeout=45, retries=1):
    """调用 DeepSeek，返回文本。json_mode 时强制 JSON 对象输出。

    retries 默认 1：重试是保底手段，默认值过大只会让单次咨询多花调用费。
    """
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


def _strip_fence(text):
    """模型有时把 JSON 包在 ```json 代码块里，剥掉再解析，省掉一次重试调用。"""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t
        if t.endswith("```"):
            t = t[:-3]
    return t.strip()


def chat_hedged(messages, *, hedge_after=0.9, timeout=45, **kw):
    """对冲请求：先发一个；超过 hedge_after 秒没回来，再发一个同样的，取先到的。

    只治「单次偶发卡 4–5 秒」这种尾延迟，正常情况下只花一次调用。
    """
    q = queue.Queue()

    def worker():
        try:
            q.put(("ok", chat(messages, timeout=timeout, **kw)))
        except Exception as e:  # noqa: BLE001
            q.put(("err", e))

    threading.Thread(target=worker, daemon=True).start()
    try:
        status, payload = q.get(timeout=hedge_after)
    except queue.Empty:
        threading.Thread(target=worker, daemon=True).start()
        try:
            status, payload = q.get(timeout=timeout)
        except queue.Empty:
            raise LLMError("hedged request timed out")

    if status == "ok":
        return payload
    # 先到的是错误：再给第二个一次机会
    try:
        status2, payload2 = q.get(timeout=timeout * 0.6)
        if status2 == "ok":
            return payload2
        raise payload2
    except queue.Empty:
        raise payload


def chat_json(messages, hedge=False, **kw):
    """要求返回 JSON，解析失败时重试一次。hedge=True 时走对冲请求。"""
    fn = chat_hedged if hedge else chat
    text = _strip_fence(fn(messages, json_mode=True, **kw))
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        retry = messages + [
            {"role": "assistant", "content": text},
            {"role": "user", "content": "上一条不是合法 JSON。请只输出 JSON 对象，不要任何解释。"},
        ]
        text2 = _strip_fence(fn(retry, json_mode=True, **kw))
        return json.loads(text2)
