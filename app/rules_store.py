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

# 支持的市场码。以前漏了 UK / JP，导致库里明明有这两国规则、商家却加不了新的（2026-11-04 修）。
MARKETS = ("CN", "EU", "US", "UK", "JP", "KR", "PH", "RU", "MN", "*")

# 编辑表格里，列表型字段用分隔符拼成一格给人改
_SEPS = (",", "，", "、", ";", "；")


def _split(value):
    """把「最佳、第一，唯一」这种一格文本拆回列表。"""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value)
    for sep in _SEPS[1:]:
        text = text.replace(sep, ",")
    return [part.strip() for part in text.split(",") if part.strip()]


def _join(value):
    return "、".join(str(x) for x in (value or []))


def to_editor_rows(rules):
    """规则对象 -> 后台可编辑表格的行（列表字段拼成文本，方便直接改/新增）。"""
    rows = []
    for r in rules:
        rows.append({
            "id": r.get("id", ""),
            "market": r.get("market", ""),
            "category": r.get("category", "*"),
            "level": r.get("level", "L1"),
            "action": r.get("action", "block"),
            "clause": r.get("clause", ""),
            "trigger": r.get("trigger", ""),
            "触发词·中文": _join(r.get("patterns")),
            "触发词·英文": _join(r.get("patterns_en")),
            "豁免情形": _join(r.get("exempt")),
            "verified": "示例·待核实" if r.get("unverified") else "已核对",
        })
    return rows


def from_editor_rows(rows, original=None):
    """编辑表格的行 -> 规则对象。

    original 是保存前的旧规则列表：表格里看不到的字段（patterns_regex / requires 等）
    按 id 原样保留，避免改一条规则时把正则丢了。
    """
    orig = {}
    for r in (original or []):
        orig[str(r.get("id", "")).strip()] = r
    out = []
    for row in rows:
        rid = str(row.get("id") or "").strip()
        rule = dict(orig.get(rid, {}))
        for key in ("id", "clause", "trigger", "category"):
            val = row.get(key)
            rule[key] = "" if val is None else str(val).strip()
        rule["id"] = rid
        rule["market"] = str(row.get("market") or "").strip().upper()
        rule["level"] = str(row.get("level") or "").strip().upper()
        rule["action"] = str(row.get("action") or "").strip().lower()
        rule["category"] = rule["category"] or "*"
        rule["patterns"] = _split(row.get("触发词·中文"))
        rule["patterns_en"] = _split(row.get("触发词·英文"))
        rule["exempt"] = _split(row.get("豁免情形"))
        rule["unverified"] = ("待核实" in str(row.get("verified") or ""))
        out.append(rule)
    return out


def _ensure():
    DATA.mkdir(exist_ok=True)
    VERSIONS.mkdir(exist_ok=True)
    if not RUNTIME.exists():
        shutil.copyfile(RULES, RUNTIME)
        return
    # 出厂规则（rules.json）比运行时副本新 —— 说明代码/数据发过新版本，
    # 以出厂为准覆盖一次。商家编辑只会更新 runtime 的 mtime，不会被这里盖掉。
    try:
        if RULES.stat().st_mtime > RUNTIME.stat().st_mtime + 1:
            shutil.copyfile(RULES, RUNTIME)
    except OSError:
        pass


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
        if str(r["market"]).upper() not in MARKETS:
            errors.append("第 %d 条：市场码 %s 不支持（可用：%s）"
                          % (i, r["market"], " / ".join(MARKETS)))
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
