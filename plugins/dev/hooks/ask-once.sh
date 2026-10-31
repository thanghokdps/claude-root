#!/usr/bin/env bash
# ask-once.sh — the user is asked everything before the build, never during it.
# UserPromptSubmit: a new turn clears the state. PostToolUse(Edit|Write|MultiEdit|NotebookEdit): an edit to a
# project file outside specs/, docs/ (ADRs, feature docs, tickets) and a plans/ dir marks the build started. PreToolUse(AskUserQuestion): once
# started, the first question of the turn is denied with a pointer to the debate in references/auto-decisions.md;
# a second call passes, so a confirmation no rollback undoes (push, merge, deploy, delete) still reaches the user.
# Stop: once started, a reply whose last line is a question is blocked once (stop_hook_active lets the retry end).
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


def last_line_is_question(path):
    # the transcript's last assistant text, last non-empty line; only the tail is read, so a long session stays cheap
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 200_000))
            raw = f.read().decode("utf-8", "replace")
    except OSError:
        return False
    text = ""
    for line in raw.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") != "assistant":
            continue
        content = (e.get("message") or {}).get("content")
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content or []
        texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
        if any(t.strip() for t in texts):
            text = "\n".join(texts)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return bool(lines) and lines[-1].rstrip("*_` ").endswith(("?", "？"))


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
        if not path or re.search(r"(^|/)(specs|docs|plans)/", path):
            sys.exit(0)
        cwd = ev.get("cwd") or ""
        if cwd and os.path.isabs(path) and not (path + "/").startswith(cwd.rstrip("/") + "/"):
            sys.exit(0)  # a scratch file outside the project is not the build
        os.makedirs(state_dir, exist_ok=True)
        if not os.path.exists(state):
            with open(state, "w") as f:
                f.write("started")
        sys.exit(0)

    if event == "PreToolUse" and ev.get("tool_name") != "AskUserQuestion" or event not in ("PreToolUse", "Stop"):
        sys.exit(0)
    with open(state) as f:
        status = f.read().strip()
except OSError:
    sys.exit(0)

if event == "Stop":
    if ev.get("stop_hook_active") or not last_line_is_question(ev.get("transcript_path") or ""):
        sys.exit(0)
    print(json.dumps({"decision": "block", "reason": (
        "ask-once: the build has started, but your reply ends with a question to the user. Settle it with "
        "/resolve-question (subagents debate, you judge), record it under Decided for you with why: and revert:, "
        "and end with the result instead. A confirmation no rollback undoes (push, merge, deploy, delete) may "
        "stay: stop again and it passes.")}))
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
