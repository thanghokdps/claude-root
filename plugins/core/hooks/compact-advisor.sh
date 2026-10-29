#!/usr/bin/env bash
# compact-advisor.sh — tell the user when the session's context is large enough that /compact is worth it.
# Trigger: Stop. Reads the last assistant usage in the transcript (input + cache tokens = the context the
# model just read) and, past CLAUDE_COMPACT_ADVISE_TOKENS (default 200000), shows one line to the user via
# systemMessage. It costs no tokens: the model never sees it. Repeats only after another
# CLAUDE_COMPACT_ADVISE_STEP tokens (default 100000) of growth. Never blocks. 0 turns it off.
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 -I - <<'PY'
import json, os, re, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
try:
    limit = int(os.environ.get("CLAUDE_COMPACT_ADVISE_TOKENS", "200000"))
    step = int(os.environ.get("CLAUDE_COMPACT_ADVISE_STEP", "100000"))
except ValueError:
    sys.exit(0)
path = ev.get("transcript_path") or ""
if limit <= 0 or ev.get("stop_hook_active") or not os.path.isfile(path):
    sys.exit(0)

used = 0
try:
    with open(path, "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 400_000))
        tail = f.read().decode("utf-8", "replace").splitlines()
except OSError:
    sys.exit(0)
for line in reversed(tail):
    try:
        e = json.loads(line)
    except ValueError:
        continue
    u = (e.get("message") or {}).get("usage") if e.get("type") == "assistant" else None
    if u:
        used = sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
        break
if used < limit:
    sys.exit(0)

state = os.path.join(os.environ.get("TMPDIR", "/tmp"), "claude-compact-advisor",
                     re.sub(r"[^A-Za-z0-9_.-]", "_", ev.get("session_id") or "nosession"))
try:
    last = int(open(state).read().strip())
except (OSError, ValueError):
    last = 0
if last and used < last + step:
    sys.exit(0)
try:
    os.makedirs(os.path.dirname(state), exist_ok=True)
    open(state, "w").write(str(used))
except OSError:
    pass
print(json.dumps({"systemMessage": f"Context is at {used // 1000}k tokens. At the next break between tasks, "
                  "run /compact (or /core:compact to keep a handoff) so later answers stay sharp and cheaper."}))
sys.exit(0)
PY
