#!/usr/bin/env bash
# test-lock.sh — while a bug's regression test is locked, the fix can't be made by changing the test.
# Trigger: PreToolUse(Edit|Write|MultiEdit|NotebookEdit|Bash). Active only when <git-dir>/claude-fix-lock.json exists
# (written by fix-bug's scripts/lock-tests.sh). Blocks (exit 2):
#   - Edit/Write/MultiEdit/NotebookEdit of a locked file
#   - Bash that mentions the lock file other than through lock-tests.sh
#   - Bash `git checkout|restore|rm|mv|stash`, or `rm`/`mv`, that names a locked file
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 - <<'PY'
import json, os, re, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
tool, ti = ev.get("tool_name", ""), ev.get("tool_input") or {}


def git(*args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


git_dir = git("rev-parse", "--absolute-git-dir")
top = git("rev-parse", "--show-toplevel")
if not git_dir or not top:
    sys.exit(0)
try:
    locked = json.load(open(os.path.join(git_dir, "claude-fix-lock.json"), encoding="utf-8")).get("files", [])
except (OSError, ValueError):
    sys.exit(0)
top = os.path.realpath(top)
paths = {os.path.realpath(os.path.join(top, e["path"])): e["path"] for e in locked if e.get("path")}


def block(msg):
    print(msg, file=sys.stderr)
    sys.exit(2)


if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
    target = ti.get("file_path") or ti.get("notebook_path") or ""
    if not target:
        sys.exit(0)
    full = os.path.realpath(target if os.path.isabs(target) else os.path.join(cwd, target))
    if full in paths:
        block(f"test-lock: {paths[full]} reproduces the bug being fixed and is locked. Fix the code, not the test; "
              "run lock-tests.sh check, then unlock after the commit.")
    sys.exit(0)

if tool != "Bash":
    sys.exit(0)
cmd = ti.get("command") or ""
AT = r"(?:^|[;&|(]|\n)\s*(?:[A-Za-z_]\w*=\S*\s+)*"
if "claude-fix-lock.json" in cmd and not re.search(AT + r"(?:bash\s+|sh\s+)?\S*lock-tests\.sh\b", cmd):
    block("test-lock: the fix lock is managed only through lock-tests.sh (lock | check | unlock).")

# A bare stash also sweeps up the uncommitted locked test, so it needs no path to be blocked.
if re.search(AT + r"git(?:\s+-[Cc]\s+\S+)*\s+stash\b", cmd):
    block("test-lock: git stash would shelve the locked regression test. Unlock first, with the user's yes if the test is wrong.")

mutates = re.search(AT + r"(?:git(?:\s+-[Cc]\s+\S+)*\s+(?:checkout|restore|rm|mv|stash)|rm|mv)\b", cmd)
if mutates:
    for full, rel in paths.items():
        names = {rel, os.path.basename(rel), full}
        if any(re.search(r"(?<![\w./-])" + re.escape(n) + r"(?![\w-])", cmd) for n in names):
            block(f"test-lock: {rel} reproduces the bug being fixed and is locked; this command would change it. "
                  "Fix the code, not the test; unlock only after the commit.")
sys.exit(0)
PY
