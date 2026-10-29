#!/usr/bin/env bash
# ticket-ledger.sh — record which skills and subagents ran on each branch, for ticket-gate.sh.
#   PostToolUse(Skill), UserPromptExpansion (a typed /command) → {"kind": "skill", "name": ...}
#   PostToolUse(Agent|Task) → {"kind": "agent", "type": ..., "model": ...}
# One JSON line per event in <git-dir>/claude-ticket-ledger.jsonl: inside .git, so it is never committed.
# Never blocks: always exits 0.
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 -I - <<'PY' || true
import json, os, subprocess, sys, time

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def git(*args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


git_dir = git("rev-parse", "--absolute-git-dir")
if not git_dir:
    sys.exit(0)
event, tool = ev.get("hook_event_name", ""), ev.get("tool_name", "")
ti = ev.get("tool_input") or {}
if event == "UserPromptExpansion":
    entry = {"kind": "skill", "name": ev.get("command_name") or ""}
elif tool == "Skill":
    entry = {"kind": "skill", "name": ti.get("skill") or ""}
elif tool in ("Agent", "Task"):
    entry = {"kind": "agent", "type": ti.get("subagent_type") or "", "model": ti.get("model") or ""}
else:
    sys.exit(0)
if entry.get("kind") == "skill":
    entry["name"] = entry["name"].lstrip("/").rpartition(":")[2]
    if not entry["name"]:
        sys.exit(0)
entry.update(branch=git("symbolic-ref", "--short", "HEAD"), at=int(time.time()), session=ev.get("session_id", ""))
with open(os.path.join(git_dir, "claude-ticket-ledger.jsonl"), "a") as f:
    f.write(json.dumps(entry) + "\n")
PY
exit 0
