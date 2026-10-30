#!/usr/bin/env bash
# ask-once.sh — the user is asked everything before the build, never during it.
# UserPromptSubmit: a new turn clears the state. PostToolUse(Edit|Write|MultiEdit|NotebookEdit): an edit to a
# file outside specs/, docs/tickets/ and a plans/ dir marks the build started. PreToolUse(AskUserQuestion): once
# started, the first question of the turn is denied with a pointer to the debate in references/auto-decisions.md;
# a second call passes, so a confirmation no rollback undoes (push, merge, deploy, delete) still reaches the user.
# State: $TMPDIR/claude-ask-once/<session_id>. Never blocks on its own failure: any error exits 0.
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 -I - <<'PY'
import json, os, re, sys, tempfile

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
sid = ev.get("session_id") or ""
if not re.fullmatch(r"[A-Za-z0-9_-]+", sid):
    sys.exit(0)
state_dir = os.path.join(tempfile.gettempdir(), "claude-ask-once")
state = os.path.join(state_dir, sid)
event = ev.get("hook_event_name")

try:
    if event == "UserPromptSubmit":
        if os.path.exists(state):
            os.remove(state)
        sys.exit(0)

    if event == "PostToolUse":
        path = (ev.get("tool_input") or {}).get("file_path") or (ev.get("tool_input") or {}).get("notebook_path") or ""
        if not path or re.search(r"(^|/)(specs|docs/tickets|plans)/", path):
            sys.exit(0)
        os.makedirs(state_dir, exist_ok=True)
        if not os.path.exists(state):
            with open(state, "w") as f:
                f.write("started")
        sys.exit(0)

    if event != "PreToolUse" or ev.get("tool_name") != "AskUserQuestion":
        sys.exit(0)
    with open(state) as f:
        status = f.read().strip()
except OSError:
    sys.exit(0)

if status != "started":
    sys.exit(0)
try:
    with open(state, "w") as f:
        f.write("nudged")
except OSError:
    sys.exit(0)
reason = (
    "ask-once: the build has started, so the user is not asked again. Settle this choice with /resolve-question: "
    "subagents debate the options, you judge, and the pick is recorded with challenged: and revert: under "
    "Decided for you (dev references/auto-decisions.md). Only a confirmation no rollback undoes (push, merge, "
    "deploy, delete) goes to the user: call AskUserQuestion again and it passes."
)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                         "permissionDecisionReason": reason}}))
PY
exit 0
