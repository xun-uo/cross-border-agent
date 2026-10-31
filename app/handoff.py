# -*- coding: utf-8 -*-
"""人工接管通道：AI 判不了的会话进待处理池，商家后台回复，买家刷新可取到。

Streamlit 不支持服务端推送，所以这里是「共享内存 + 拉取」模型：
买家每次页面重跑（发消息 / 手动刷新）时检查有没有新的人工回复。
进程内共享；实例重启后清空（演示够用）。
"""
import threading
import time

_LOCK = threading.Lock()
_SESSIONS = {}  # sid -> dict


def _now():
    return time.strftime("%H:%M")


def ensure(sid, market="", language="zh", buyer=""):
    with _LOCK:
        s = _SESSIONS.get(sid)
        if s is None:
            s = {
                "sid": sid,
                "created": _now(),
                "market": market,
                "language": language,
                "buyer": buyer,
                "status": "ai",       # ai / pending / answered / closed
                "mode": "ai",         # ai = AI 处理；human = 人工接管中
                "messages": [],       # {role, text, ts, source}
                "reply_idx": 0,       # 买家已消费到第几条人工回复
            }
            _SESSIONS[sid] = s
        return s


def add_message(sid, role, text, source="ai"):
    s = ensure(sid)
    with _LOCK:
        s["messages"].append({"role": role, "text": text, "ts": _now(), "source": source})
        if source == "human":
            s["status"] = "answered"


def mark_pending(sid, reason=""):
    s = ensure(sid)
    with _LOCK:
        if s["status"] == "ai":
            s["status"] = "pending"
            s["reason"] = reason


def pending():
    """待人工处理的会话，最新的在前。"""
    with _LOCK:
        out = [dict(s) for s in _SESSIONS.values() if s["status"] == "pending"]
    out.sort(key=lambda x: x["created"], reverse=True)
    return out


def all_sessions():
    with _LOCK:
        return [dict(s) for s in _SESSIONS.values()]


def get(sid):
    with _LOCK:
        s = _SESSIONS.get(sid)
        return dict(s) if s else None


def human_reply(sid, text):
    s = ensure(sid)
    with _LOCK:
        s["messages"].append({"role": "assistant", "text": text,
                              "ts": _now(), "source": "human"})
        s["status"] = "answered"
    return True


def pull_replies(sid):
    """买家端调用：取尚未消费的人工回复，并把游标推到末尾。"""
    with _LOCK:
        s = _SESSIONS.get(sid)
        if not s:
            return []
        human = [m for m in s["messages"] if m.get("source") == "human"]
        new = human[s["reply_idx"]:]
        s["reply_idx"] = len(human)
        return list(new)


def close(sid):
    s = ensure(sid)
    with _LOCK:
        s["status"] = "closed"


def mark_handled(sid):
    s = ensure(sid)
    with _LOCK:
        if s["status"] in ("pending", "answered"):
            s["status"] = "handled"

def enter_human(sid):
    """转入人工模式：此后买家消息都不走 AI。"""
    s = ensure(sid)
    with _LOCK:
        s["mode"] = "human"
        if s["status"] == "ai":
            s["status"] = "pending"


def back_to_ai(sid):
    """人工结束会话，交还 AI。"""
    s = ensure(sid)
    with _LOCK:
        s["mode"] = "ai"
        s["status"] = "handled"


def is_human_mode(sid):
    s = get(sid)
    return bool(s and s.get("mode") == "human")
