#!/usr/bin/env bash
# plan-recall.sh — an active PLAN.md is recalled every turn, so /clear or a compaction never loses the slice.
# Trigger: UserPromptSubmit. Reads specs/*/PLAN.md under the project (the event's cwd, else the git toplevel)
# whose `**Status:**` is active — the two most recently touched — and injects each one's path, first open task
# (a <task> without status="done"; format in ${CLAUDE_PLUGIN_ROOT}/references/plan-format.md) and the last 3
# lines of its ## Status log, ~1500 chars in all. draft, paused and complete plans are silent. The Stop side
# is plan-gate.sh. Ported from OthmanAdi/planning-with-files hooks/claude-hook.sh (user-prompt-submit →
# scripts/inject-plan.sh). Never blocks and never fails: any error of its own exits 0.
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 -I - <<'PY'
import glob, json, os, re, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
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


def tasks(text):
    out = []
    for attrs, body in re.findall(r"<task\b([^>]*)>(.*?)</task>", text, re.S):
        a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
        action = re.search(r"<action>(.*?)</action>", body, re.S)
        title = " ".join((action.group(1) if action else "").split())[:80]
        out.append((a.get("id", "?"), a.get("status", "").lower() == "done", title))
    return out


def log_tail(text, n=3):
    m = re.search(r"^## Status log\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    lines = [ln.strip() for ln in (m.group(1) if m else "").splitlines() if ln.strip()]
    return lines[-n:]


plans = sorted(glob.glob(os.path.join(root, "specs", "*", "PLAN.md")), key=os.path.getmtime, reverse=True)
chunks = []
for path in plans:
    text = read(path)
    if status(text) != "active":
        continue
    rel = os.path.relpath(path, root)
    ts = tasks(text)
    done = sum(1 for _, d, _ in ts if d)
    nxt = next(((i, t) for i, d, t in ts if not d), None)
    head = f"Active plan {rel} ({done}/{len(ts)} tasks done)"
    head += f" — next: task {nxt[0]} '{nxt[1]}'" if nxt else " — every task is done: set **Status:** complete"
    tail = log_tail(text)
    chunks.append(head + ("\nStatus log:\n" + "\n".join(tail) if tail else ""))
    if len(chunks) == 2:
        break
if not chunks:
    sys.exit(0)
ctx = "\n\n".join(chunks)[:1400]
ctx += ("\n\nMark a finished task with status=\"done\" on its <task>, append to ## Status log, set **Status:** "
        "complete at the end or paused to set the plan aside (dev references/plan-format.md).")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))
PY
exit 0
