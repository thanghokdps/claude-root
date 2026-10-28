#!/usr/bin/env bash
# auto-decisions.sh — on a high-risk ticket worked without the user (auto mode), every choice Claude made for
# the user is written down and argued against before the session stops.
# Trigger: Stop. Applies when permission_mode is auto or bypassPermissions (or CLAUDE_AUTO_DECISIONS=1), the
# branch is <type>/<id>-<slug> and docs/tickets/<id>/plan.md says `Risk: high`. Blocks the stop once when
# plan.md has no `## Auto decisions` section, or an entry in it has no `challenged:` part. An entry
# `- none: <why>` records that every choice was the user's. Format: ${CLAUDE_PLUGIN_ROOT}/references/auto-decisions.md
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 - <<'PY'
import json, os, re, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
auto = ev.get("permission_mode") in ("auto", "bypassPermissions") or os.environ.get("CLAUDE_AUTO_DECISIONS") == "1"
if not auto or ev.get("stop_hook_active"):
    sys.exit(0)
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def git(*args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


branch, top = git("symbolic-ref", "--short", "HEAD"), git("rev-parse", "--show-toplevel")
m = re.match(r"^[\w.-]+/([A-Za-z]+-\d+|\d+)(?:[-_]|$)", branch)
if not m or not top:
    sys.exit(0)
plan_path = os.path.join(top, "docs", "tickets", m.group(1), "plan.md")
try:
    plan = open(plan_path, encoding="utf-8").read()
except OSError:
    sys.exit(0)
if not re.search(r"(?im)^[\s*>-]*Risk\**\s*:\**\s*`?high\b", plan):
    sys.exit(0)

section = re.search(r"(?ims)^##\s+Auto decisions\s*$(.*?)(?=^##\s|\Z)", plan)
entries = re.findall(r"(?m)^\s*[-*]\s+(.+)$", section.group(1)) if section else []
problem = ""
if not entries:
    problem = "has no `## Auto decisions` section listing the choices you made for the user"
else:
    open_ = [e for e in entries if not re.match(r"(?i)none\b", e) and not re.search(r"(?i)\bchallenged\s*:", e)]
    if open_:
        problem = f"has {len(open_)} auto decision(s) without a `challenged:` result, e.g. “{open_[0][:80]}”"
if not problem:
    sys.exit(0)
rel = os.path.relpath(plan_path, top)
print(json.dumps({"decision": "block", "reason": (
    f"auto-decisions: this is a Risk: high ticket worked in auto mode, and {rel} {problem}. "
    "For each choice the user did not make, dispatch one cheap subagent (model: haiku) per rejected option "
    "to argue for it, then record `- <decision> · options: … · chose … because … · challenged: <best "
    "counter-argument> → kept | switched`. If the user made every choice, add `- none: <why>`.")}))
sys.exit(0)
PY
