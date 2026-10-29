# -*- coding: utf-8 -*-
"""规则库读写：支持商家后台的导入、编辑、启停与版本回滚。

正式产品应落数据库；当前用 JSON 文件 + 版本快照，
在 Streamlit Cloud 上重启会回到初始状态（演示够用）。
"""
import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RULES = DATA / "rules.json"
RUNTIME = DATA / "rules_runtime.json"
VERSIONS = DATA / "rule_versions"


def _ensure():
    DATA.mkdir(exist_ok=True)
    VERSIONS.mkdir(exist_ok=True)
    if not RUNTIME.exists():
        shutil.copyfile(RULES, RUNTIME)


def load():
    _ensure()
    return json.loads(RUNTIME.read_text(encoding="utf-8"))


def save(rules, note="manual edit"):
    _ensure()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    VERSIONS.mkdir(exist_ok=True)
    (VERSIONS / (stamp + ".json")).write_text(
        json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    RUNTIME.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(rules)


def versions():
    _ensure()
    return sorted([p.stem for p in VERSIONS.glob("*.json")], reverse=True)


def rollback(stamp):
    _ensure()
    src = VERSIONS / (stamp + ".json")
    if not src.exists():
        raise FileNotFoundError(stamp)
    RUNTIME.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def reset_default():
    _ensure()
    shutil.copyfile(RULES, RUNTIME)


def validate(rows):
    """返回 (ok_rows, errors)。errors 带行号与原因。"""
    ok, errors, seen = [], [], set()
    for i, r in enumerate(rows, start=1):
        if not isinstance(r, dict):
            errors.append("第 %d 条：不是对象" % i)
            continue
        miss = [k for k in ("id", "market", "level", "action", "clause", "trigger")
                if not str(r.get(k, "")).strip()]
        if miss:
            errors.append("第 %d 条：缺字段 %s" % (i, ", ".join(miss)))
            continue
        rid = str(r["id"]).strip()
        if rid in seen:
            errors.append("第 %d 条：id 重复（%s）" % (i, rid))
            continue
        if str(r["market"]).upper() not in ("CN", "EU", "US", "PH", "KR", "RU", "MN", "*"):
            errors.append("第 %d 条：市场码 %s 不支持" % (i, r["market"]))
            continue
        if str(r["level"]) not in ("L1", "L2", "L3"):
            errors.append("第 %d 条：级别只能是 L1/L2/L3" % i)
            continue
        if not (r.get("patterns") or r.get("patterns_en") or r.get("patterns_regex")):
            errors.append("第 %d 条：至少需要一个 patterns" % i)
            continue
        seen.add(rid)
        ok.append(r)
    return ok, errors
