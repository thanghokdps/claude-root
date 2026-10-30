#!/usr/bin/env bash
# plan-gate.sh — a turn cannot end while an active PLAN.md still has an open task.
# Trigger: Stop. Reads specs/*/PLAN.md under the project (the event's cwd, else the git toplevel); the first
# one whose `**Status:**` is active and has a <task> without status="done" blocks the stop once, naming the
# task. The retry (stop_hook_active true) always ends, so the agent can still stop after saying why. paused or
# complete plans never block: set **Status:** paused to set a plan aside. The recall side is plan-recall.sh;
# format in ${CLAUDE_PLUGIN_ROOT}/references/plan-format.md. Ported from OthmanAdi/planning-with-files
# hooks/claude-hook.sh (stop → scripts/gate-stop.sh). Never fails: any error of its own exits 0.
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 -I - <<'PY'
import glob, json, os, re, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
if ev.get("stop_hook_active"):
    sys.exit(0)
start = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
r = subprocess.run(["git", "-C", start, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
root = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else start


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read(200_000)
    except OSError:
        return ""


def status(text):
    m = re.search(r"^\*\*Status:\*\*\s*([A-Za-z]+)", text, re.M)
    return m.group(1).lower() if m else ""


def first_open_task(text):
    for attrs, body in re.findall(r"<task\b([^>]*)>(.*?)</task>", text, re.S):
        a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
        if a.get("status", "").lower() == "done":
            continue
        action = re.search(r"<action>(.*?)</action>", body, re.S)
        tid = a.get("id", "")
        # the title is plan text quoted as data: whitespace-collapsed and capped, the id a strict token
        return (tid if re.fullmatch(r"[0-9A-Za-z._-]{1,16}", tid) else "?",
                " ".join((action.group(1) if action else "").split())[:80])
    return None


for path in sorted(glob.glob(os.path.join(root, "specs", "*", "PLAN.md")), key=os.path.getmtime, reverse=True):
    text = read(path)
    if status(text) != "active":
        continue
    task = first_open_task(text)
    if not task:
        continue
    rel = os.path.relpath(path, root)
    print(json.dumps({"decision": "block", "reason": (
        f"PLAN {rel}: task {task[0]} '{task[1]}' not done — finish it, mark it status=\"done\" in PLAN.md, "
        "or set **Status:** paused (dev references/plan-format.md). Stop again and it passes.")}))
    break
PY
exit 0
