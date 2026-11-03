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
    """会话消息/时间戳一律北京时间（#44：线上容器是 UTC，原来会慢 8 小时）。"""
    from app import clock
    return clock.hhmm()


def ensure(sid, market="", language="zh", buyer="", order_no=""):
    with _LOCK:
        s = _SESSIONS.get(sid)
        if s is None:
            s = {
                "sid": sid,
                "created": _now(),
                "market": market,
                "language": language,
                "buyer": buyer,
                # 绑定的订单号：买家退出重登时靠它找回旧会话（#42）。
                # 只做「内存里还在就复用」，服务重启后自然清空 —— 用户定的口径。
                "order_no": order_no or "",
                "status": "ai",       # ai / pending / answered / closed
                "mode": "ai",         # ai = AI 处理；human = 人工接管中
                "pending_since": None,
                "comforted": False,
                "messages": [],       # {role, text, ts, source}
                "reply_idx": 0,       # 买家已消费到第几条人工回复
                "owner": None,        # 接管这个会话的客服账号（None = 还没人接）
                "last_activity": time.time(),  # 最后一次有人说话的时间，用于超时释放
                # 未读红点用：买家最后说话的时刻 / 客服最后打开这个会话的时刻。
                # 红点数 = last_buyer_ts > agent_viewed_ts 的会话数（见 unread_count）。
                "last_buyer_ts": 0.0,
                "agent_viewed_ts": 0.0,
            }
            _SESSIONS[sid] = s
        elif order_no and not s.get("order_no"):
            # 老会话是 #42 之前建的、没记订单号：补上，下次登录才找得到
            s["order_no"] = order_no
        return s


def by_order(order_no, limit_age=None):
    """按订单号找回最近一条会话（#42：买家退出重登后接着聊）。

    只在进程内存里找 —— 服务重启就没了，这是用户明确接受的行为（不落盘）。
    limit_age 给一个秒数可以只认「最近这么久之内」的会话，默认不限。
    """
    order_no = (order_no or "").strip()
    if not order_no:
        return None
    now = time.time()
    with _LOCK:
        cands = [dict(s) for s in _SESSIONS.values() if s.get("order_no") == order_no]
    if limit_age:
        cands = [c for c in cands if now - float(c.get("last_activity") or 0) <= limit_age]
    if not cands:
        return None
    # 优先「最后有人说的话」最新的那条；都空就按创建时间
    cands.sort(key=lambda c: float(c.get("last_activity") or 0), reverse=True)
    return cands[0]


def add_message(sid, role, text, source="ai", image=None):
    s = ensure(sid)
    with _LOCK:
        msg = {"role": role, "text": text, "ts": _now(), "source": source}
        if image:
            msg["image"] = image
        s["messages"].append(msg)
        # 任何一方说话都算「有活动」，超时释放要从这一刻重新计时
        s["last_activity"] = time.time()
        if source == "buyer":
            # 买家说话 = 有未读（商家还没打开看过）
            s["last_buyer_ts"] = s["last_activity"]
        if source == "human":
            s["status"] = "answered"
        elif source == "buyer" and s.get("mode") == "human":
            # 买家在人工模式下发新消息 → 重新进入待处理。
            # 否则商家回复过一次之后 status 停在 handled，买家再追问就永远不出现在待处理列表里，
            # 商家看不见、买家干等。
            s["status"] = "pending"
            if not s.get("pending_since"):
                s["pending_since"] = time.time()


def mark_pending(sid, reason=""):
    s = ensure(sid)
    with _LOCK:
        if s["status"] == "ai":
            s["status"] = "pending"
            s["reason"] = reason


def pending():
    """人工模式下的会话，最新的在前。

    注意：这里筛的是 mode == "human"，不是 status == "pending"。
    商家回复一次之后 status 会变成 answered/handled，如果按 status 筛，
    会话会从列表里直接消失——商家看不见历史，想补一句话都没入口。
    只有点了「交还 AI」把 mode 改回 ai，才会从列表里移除。
    """
    with _LOCK:
        out = [dict(s) for s in _SESSIONS.values() if s.get("mode") == "human"]
    out.sort(key=lambda x: x.get("created"), reverse=True)
    return out


def all_sessions():
    with _LOCK:
        return [dict(s) for s in _SESSIONS.values()]


def finished(limit=30):
    """已经处理完的会话：交还 AI 的（mode == "ai"），供商家在「会话记录」里回看。

    这些会话没有从 _SESSIONS 里删掉，只是不再进待处理池，
    所以原样能取出来重新展示——买家说的话、AI 的回复、人工的回复都在 messages 里。
    额外标一个 had_human，方便界面上区分「纯 AI 服务」和「人工处理过」。
    """
    with _LOCK:
        out = []
        for s in _SESSIONS.values():
            if s.get("mode") != "ai":
                continue
            if not s.get("messages"):
                continue
            d = dict(s)
            d["had_human"] = any(m.get("source") == "human"
                                 for m in s.get("messages") or [])
            out.append(d)
    out.sort(key=lambda x: x.get("created") or "", reverse=True)
    return out[:limit]


def get(sid):
    with _LOCK:
        s = _SESSIONS.get(sid)
        return dict(s) if s else None


def human_reply(sid, text, agent_name="", agent_key=""):
    s = ensure(sid)
    with _LOCK:
        # 第一次人工回复 = 真正接管的时刻，先插一条系统小字，
        # 让买家知道「现在换人了」，而不是突然冒出一句话
        first = not any(m.get("source") == "human" for m in s["messages"])
        if first:
            who = (agent_name or "").strip() or "人工客服"
            s["messages"].append({"role": "assistant",
                                  "text": f"{who} 已接入，为您服务",
                                  "ts": _now(), "source": "note"})
        s["messages"].append({"role": "assistant", "text": text,
                              "ts": _now(), "source": "human"})
        s["status"] = "answered"
        # 谁先回，会话就归谁：其他客服的列表里不再出现
        if agent_key:
            s["owner"] = agent_key
        s["last_activity"] = time.time()
        # 回过了就等于看过了，红点撤掉
        s["agent_viewed_ts"] = s["last_activity"]
    return True


def visible_to(agent_key, idle_seconds=600):
    """某个客服能看到的会话。

    规则（2026-11-01 用户定）：谁先回复谁接管，从其他人的列表里隐藏；
    只有两种情况释放——① 双方都静默超过 idle_seconds（默认 10 分钟，只要有一方
    还在发消息就不释放）② 客服主动点「结束会话（交还 AI）」。
    """
    now = time.time()
    out = []
    with _LOCK:
        for s in _SESSIONS.values():
            if s.get("mode") != "human":
                continue
            owner = s.get("owner")
            idle = now - float(s.get("last_activity") or s.get("pending_since") or now)
            if owner and owner != agent_key and idle < idle_seconds:
                continue          # 被别人接着，且没静默够久 → 对当前客服隐藏
            d = dict(s)
            if owner and owner != agent_key:
                d["stale_owner"] = owner   # 静默超时了，标记一下，界面上可以提示
                s["owner"] = None          # 顺手释放，让现在打开的人可以接
            out.append(d)
    out.sort(key=lambda x: x.get("created"), reverse=True)
    return out


def pull_replies(sid):
    """买家端调用：取尚未消费的人工回复与系统提示，并把游标推到末尾。"""
    with _LOCK:
        s = _SESSIONS.get(sid)
        if not s:
            return []
        human = [m for m in s["messages"] if m.get("source") in ("human", "note")]
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


def mark_viewed(sid):
    """客服打开/回复了这个会话：把「看过的时刻」推到买家最后一条之后。

    只做时间戳比较，不动 status —— 买家再说话时 last_buyer_ts 会超过它，
    红点自然又亮起来（「打开过」不等于「处理完」）。
    """
    with _LOCK:
        s = _SESSIONS.get(sid)
        if not s:
            return
        s["agent_viewed_ts"] = max(time.time(), float(s.get("last_buyer_ts") or 0))


def unread_count(agent_key="", idle_seconds=600):
    """「待处理会话」红点的数字：需要人工、且买家最后一条比客服看过的晚。

    和「未回复 / 已回复」两个折叠组不是一回事：分组看最后一条是不是人工回的，
    红点看有没有新消息没看（用户 2026-11-02 定的规则）。
    """
    n = 0
    for s in visible_to(agent_key, idle_seconds):
        if float(s.get("last_buyer_ts") or 0) > float(s.get("agent_viewed_ts") or 0):
            n += 1
    return n

def enter_human(sid):
    """转入人工模式：此后买家消息都不走 AI。"""
    s = ensure(sid)
    with _LOCK:
        s["mode"] = "human"
        if s["status"] == "ai":
            s["status"] = "pending"
        if not s.get("pending_since"):
            s["pending_since"] = time.time()


def back_to_ai(sid):
    """人工结束会话，交还 AI。"""
    s = ensure(sid)
    with _LOCK:
        s["mode"] = "ai"
        s["status"] = "handled"
        s["owner"] = None      # 交还 AI 就释放接管，下次转人工谁都能接


def is_human_mode(sid):
    s = get(sid)
    return bool(s and s.get("mode") == "human")

COMFORT = {
    # 只用来兜住「真的没人回」，所以话要短、说人话，别客套
    "zh": "人工客服还没回复。你的消息已经排上队，回过来会直接出现在这里。",
    "en": "No one from our team has replied yet. Your chat is queued — "
          "the reply will appear right here.",
    "es": "Nuestro equipo aún no ha respondido. Su consulta está en cola — "
          "la respuesta aparecerá justo aquí.",
    "vi": "Nhân viên chưa trả lời. Tin của bạn đã vào hàng đợi — "
          "phản hồi sẽ hiện ngay tại đây.",
    "th": "เจ้าหน้าที่ยังไม่ตอบ ข้อความของคุณอยู่ในคิวแล้ว "
          "คำตอบจะแสดงที่นี่เลยค่ะ",
    "id": "Agen kami belum membalas. Pesan Anda sudah masuk antrean — "
          "balasannya akan muncul di sini.",
}


def need_comfort(sid, wait_seconds=60):
    """是否需要发安抚话术：已转人工、超时未回、且还没安抚过。

    之前是 10 秒，商家刚点开会话就跳出一条长话术，像机器人在抢话。
    """
    with _LOCK:
        s = _SESSIONS.get(sid)
        if not s:
            return None
        if s.get("mode") != "human" or s.get("comforted"):
            return None
        since = s.get("pending_since")
        if not since or time.time() - since < wait_seconds:
            return None
        return s.get("language") or "zh"


def mark_comforted(sid):
    with _LOCK:
        s = _SESSIONS.get(sid)
        if s:
            s["comforted"] = True


def add_comfort_message(sid):
    """把安抚话术写进会话，并标记已安抚（直接操作原对象）。"""
    with _LOCK:
        s = _SESSIONS.get(sid)
        if not s:
            return None
        lang = s.get("language") or "zh"
        text = COMFORT.get(lang, COMFORT["zh"])
        s["messages"].append({"role": "assistant", "text": text,
                              "ts": _now(), "source": "system"})
        s["comforted"] = True
        return text
