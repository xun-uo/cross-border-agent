# -*- coding: utf-8 -*-
"""判定日志：记录每次处理的原文、市场、品类、判定结果，供商家看板统计。"""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "out" / "judge_log.jsonl"
MAX = 500


def append(record):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        record = dict(record)
        record.setdefault("ts", time.strftime("%Y-%m-%d %H:%M:%S"))
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def tail(n=50):
    if not LOG.exists():
        return []
    try:
        lines = LOG.read_text(encoding="utf-8").strip().splitlines()[-n:]
    except Exception:
        return []
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def stats():
    recs = tail(MAX)
    by_market, by_verdict, total, rewritten = {}, {}, 0, 0
    for r in recs:
        total += 1
        m = r.get("market") or "-"
        by_market[m] = by_market.get(m, 0) + 1
        v = r.get("verdict") or "-"
        by_verdict[v] = by_verdict.get(v, 0) + 1
        if v in ("rewrite", "block"):
            rewritten += 1
    return {"total": total, "by_market": by_market, "by_verdict": by_verdict,
            "rewrite_rate": round(100.0 * rewritten / total, 1) if total else 0.0}
