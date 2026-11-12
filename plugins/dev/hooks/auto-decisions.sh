#!/usr/bin/env bash
# auto-decisions.sh — on a high-risk ticket worked without the user (auto mode), every choice Claude made for
# the user is written down and argued against before the session stops.
# Trigger: Stop. Applies when permission_mode is auto or bypassPermissions (or CLAUDE_AUTO_DECISIONS=1), the
# branch is <type>/<id>-<slug> and the ticket's plan.md (specs/<id>-<slug>/ in the repo's state dir, lib/state-dir.sh
# ticket_dir) says `Risk: high`. Blocks the stop once when
# plan.md has no `## Auto decisions` section, or an entry in it has no `challenged:` part. An entry
# `- none: <why>` records that every choice was the user's. Format: ${CLAUDE_PLUGIN_ROOT}/references/auto-decisions.md
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" STATE_LIB="$(dirname "$0")/lib/state-dir.sh" python3 -I - <<'PY'
import json, os, re, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
auto = ev.get("permission_mode") in ("auto", "bypassPermissions") or os.environ.get("CLAUDE_AUTO_DECISIONS") == "1"
if not auto or ev.get("stop_hook_active"):
    sys.exit(0)
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


r = subprocess.run(["bash", "-c", '. "$1" && ticket_dir "$2"', "_", os.environ["STATE_LIB"], cwd],
                   capture_output=True, text=True)
if not r.stdout.strip():
    sys.exit(0)
plan_path = os.path.join(r.stdout.strip(), "plan.md")
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
print(json.dumps({"decision": "block", "reason": (
    f"auto-decisions: this is a Risk: high ticket worked in auto mode, and {plan_path} {problem}. "
    "For each choice the user did not make, run the debate in the dev plugin's references/auto-decisions.md "
    "(one sonnet advocate per option, a rebuttal round and an opus red team on hard gates), then record "
    "`- <decision> · options: … · chose … because … · challenged: <best counter-argument> → kept | switched "
    "· revert: <files to change>`. If the user made every choice, add `- none: <why>`.")}))
sys.exit(0)
PY
