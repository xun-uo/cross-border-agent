# -*- coding: utf-8 -*-
import json

d = json.load(open(r"D:\跨境智服\out\demo_result.json", encoding="utf-8"))
lines = []
for s in d["scenarios"]:
    lines.append(f"=== {s['id']} {s['title']}")
    if "trace" in s:
        f = s["trace"]["final"]
        lines.append(f"   verdict={f['verdict']} level={f.get('level')} handoff={f.get('handoff')} ms={s['trace'].get('ms_total')}")
        lines.append("   text=" + f["text"][:200].replace("\n", " "))
    if "draft_check" in s:
        dc = s["draft_check"]
        ev = dc["evaluation"]
        lines.append(f"   verdict={ev['verdict']} level={ev['level']} clauses={ev['clauses']}")
        lines.append(f"   rewritten={dc.get('rewritten')} passed={dc.get('rewrite_passed')} rounds={dc.get('rewrite_rounds')}")
        lines.append("   final=" + dc["final_text"][:250].replace("\n", " "))
    if "comparison" in s:
        c = s["comparison"]
        lines.append(f"   naive={c['naive_keyword']['verdict']} hits={[h['term'] for h in c['naive_keyword']['hits']]}")
        lines.append(f"   ours ={c['claim_level']['verdict']} level={c['claim_level']['level']}")
    lines.append("")
open(r"D:\跨境智服\out\summary.txt", "w", encoding="utf-8").write("\n".join(lines))
print("ok")
