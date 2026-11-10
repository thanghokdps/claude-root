#!/usr/bin/env bash
# specs-guard.sh — plans, handoffs and audits are personal: they live in the repo's state dir
# (lib/state-dir.sh), never in <repo>/specs/. Trigger: PreToolUse(Edit|Write|MultiEdit|NotebookEdit).
# Denies a write under an untracked <repo>/specs/ and names the right path; a repo that tracks specs/
# keeps them. Never fails: anything unparseable passes.
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" STATE_LIB="$(dirname "$0")/lib/state-dir.sh" python3 -I - <<'PY'
import json, os, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
ti = ev.get("tool_input") or {}
path = ti.get("file_path") or ti.get("notebook_path") or ""
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
if not path or r.returncode != 0:
    sys.exit(0)
top = os.path.realpath(r.stdout.strip())
rel = os.path.relpath(os.path.realpath(os.path.join(cwd, path)), top)
if not rel.startswith("specs" + os.sep):
    sys.exit(0)
if subprocess.run(["git", "-C", top, "ls-files", "--", "specs"], capture_output=True, text=True).stdout.strip():
    sys.exit(0)
state = subprocess.run(["bash", "-c", '. "$1" && state_dir "$2"', "_", os.environ["STATE_LIB"], top],
                       capture_output=True, text=True).stdout.strip()
if not state:
    sys.exit(0)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
    "permissionDecisionReason": f"specs/ is personal state and lives outside the repo: write "
                                f"{os.path.join(state, rel)} instead."}}))
PY
exit 0
