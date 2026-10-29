# -*- coding: utf-8 -*-
"""全面回归：演示场景 + 合规评测 + 意图 + 界面逻辑。"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:\跨境智服")
sys.path.insert(0, str(ROOT))

PY = sys.executable
lines = []


def run(cmd, name):
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    ok = r.returncode == 0
    tail = (r.stdout or "").strip().splitlines()[-6:]
    lines.append(f"[{'OK ' if ok else 'FAIL'}] {name}")
    for t in tail:
        lines.append("    " + t)
    if not ok:
        lines.append("    stderr: " + (r.stderr or "")[-300:])
    return ok


ok1 = run([PY, "run_demo.py"], "run_demo（7 场景）")
ok2 = run([PY, "scripts/eval.py", "--no-llm"], "合规评测（主集 60）")
ok3 = run([PY, "scripts/eval_gain.py"], "语义层增量（新样本 10）")

# 界面逻辑
from streamlit.testing.v1 import AppTest  # noqa: E402
at = AppTest.from_file(str(ROOT / "web" / "app.py"), default_timeout=180)
at.session_state["authed"] = True
at.session_state["history"] = []
at.session_state["last_trace"] = None
at.run()
at.chat_input[0].set_value("Does this supplement help with sleep?").run()
hist = at.session_state["history"]
tr = at.session_state.get("last_trace") or {}
steps = [s["step"] for s in tr.get("steps", [])]
lines.append(f"[{'OK ' if len(hist) == 2 else 'FAIL'}] 界面一轮问答（历史 {len(hist)} 条）")
lines.append(f"    steps={steps}")
lines.append(f"    semantic 步骤={'有' if 'semantic' in steps else '无'}")

out = "\n".join(lines)
(ROOT / "out" / "regression.txt").write_text(out, encoding="utf-8")
print(out)
