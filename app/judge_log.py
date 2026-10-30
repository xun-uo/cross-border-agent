# -*- coding: utf-8 -*-
"""判定日志（内存版）。

Streamlit Cloud 的文件系统在重启后清空、且可能被多进程隔离，
因此判定记录放在模块级列表里 —— 同一进程内商家后台一定看得到。
代价：实例重启后清空（演示够用，正式产品应落数据库）。
"""
import time

MAX = 500
_LOGS = []


def append(record):
    try:
        r = dict(record)
        r.setdefault("ts", time.strftime("%Y-%m-%d %H:%M:%S"))
        _LOGS.append(r)
        if len(_LOGS) > MAX:
            del _LOGS[: len(_LOGS) - MAX]
    except Exception:
        pass


def tail(n=50):
    try:
        return list(_LOGS[-n:])
    except Exception:
        return []


def stats():
    recs = list(_LOGS)
    by_market, by_verdict, by_category, by_lang, by_hour = {}, {}, {}, {}, {}
    clause_count = {}
    total, rewritten = 0, 0
    for r in recs:
        total += 1
        m = r.get("market") or "-"
        by_market[m] = by_market.get(m, 0) + 1
        v = r.get("verdict") or "-"
        by_verdict[v] = by_verdict.get(v, 0) + 1
        cat = r.get("category") or "-"
        by_category[cat] = by_category.get(cat, 0) + 1
        lang = r.get("language") or "-"
        by_lang[lang] = by_lang.get(lang, 0) + 1
        ts = str(r.get("ts") or "")
        hour = ts[11:13] if len(ts) >= 13 else "-"
        by_hour[hour] = by_hour.get(hour, 0) + 1
        for cl in (r.get("clauses") or []):
            clause_count[cl] = clause_count.get(cl, 0) + 1
        if v in ("rewrite", "block"):
            rewritten += 1

    top_clauses = sorted(clause_count.items(), key=lambda x: -x[1])[:5]
    return {"total": total, "by_market": by_market, "by_verdict": by_verdict,
            "by_category": by_category, "by_lang": by_lang, "by_hour": by_hour,
            "top_clauses": top_clauses,
            "rewrite_rate": round(100.0 * rewritten / total, 1) if total else 0.0}
