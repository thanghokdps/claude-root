#!/usr/bin/env bash
# test-lock.sh — while a bug's regression test is locked, the fix can't be made by changing the test.
# Trigger: PreToolUse(Edit|Write|MultiEdit|NotebookEdit|Bash). Active only when <git-dir>/claude-fix-lock.json exists
# (written by fix-bug's scripts/lock-tests.sh). Blocks (exit 2):
#   - Edit/Write/MultiEdit/NotebookEdit of a locked file
#   - Bash that names the lock file; git stash, clean, reset --hard, checkout/restore .
#   - Bash that names a locked file with git checkout|restore|rm|mv, rm, mv, cp, tee, sed, perl or a redirect
# Asks: lock-tests.sh unlock (the user confirms the fix is committed or the test is wrong).
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
# lock-tests.sh finds the lock itself, so a command that names the lock file is going around it.
if "claude-fix-lock.json" in cmd:
    block("test-lock: the fix lock is managed only through lock-tests.sh (lock | check | unlock).")

if re.search(AT + r"(?:bash\s+|sh\s+)?\S*lock-tests\.sh\s+unlock\b", cmd):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                             "permissionDecisionReason": "test-lock: unlocking the regression test. "
                                             "Approve after the fix is committed, or when you agree the test is wrong."}}))
    sys.exit(0)

# These sweep up the uncommitted locked test without naming it.
GIT = AT + r"git(?:\s+-[Cc]\s+\S+)*\s+"
if re.search(GIT + r"(?:stash\b|clean\b|reset\b[^;&|\n]*--(?:hard|merge|keep)|(?:checkout|restore)\b[^;&|\n]*\s\.(?:\s|$))", cmd):
    block("test-lock: this git command would undo or shelve the locked regression test. "
          "Unlock first, with the user's yes if the test is wrong.")

# A folder pathspec (git checkout -- src/, rm -r src) reaches the locked test without naming it.
if re.search(AT + r"(?:git(?:\s+-[Cc]\s+\S+)*\s+(?:checkout|restore|rm)|rm)\b", cmd):
    # (resolved path, is a glob prefix): a folder reaches what is under it, a glob prefix reaches any name it starts.
    reached = []
    for seg in re.split(r"&&|\|\||[;|\n]", cmd):
        words, bases, chain = re.split(r"[\s()]+", seg.strip()), {cwd}, cwd  # a git -C applies to its own command only
        for i, w in enumerate(words):
            if i and words[i - 1] == "-C":  # chained -C dirs resolve from the previous one, as git does
                chain = os.path.realpath(os.path.join(chain, os.path.expanduser(w.strip("'\""))))
                bases.add(chain)
                continue
            w = re.sub(r"^:(?:\([^)]*\)|[!^/]*)", "", w.strip("'\""))  # pathspec magic (:/src, :(glob)src)
            if w.startswith("-") or not w:
                continue
            glob_at = re.search(r"[*?\[]", w)
            literal = w[:glob_at.start()] if glob_at else w
            for base in bases:
                full = os.path.realpath(os.path.join(base, os.path.expanduser(literal)))
                reached.append((full + (os.sep if literal.endswith("/") or not literal else ""), bool(glob_at)))
    for full, rel in paths.items():
        if any(full.startswith(r) if g else (r != full and full.startswith(r.rstrip(os.sep) + os.sep))
               for r, g in reached):
            block(f"test-lock: this command reaches the folder of {rel}, which is locked. "
                  "Name the files you mean, or unlock first with the user's yes.")

mutates = re.search(AT + r"(?:git(?:\s+-[Cc]\s+\S+)*\s+(?:checkout|restore|rm|mv)|rm|mv|cp|tee|truncate|install|ln|sed|perl)\b", cmd)
written = [m.group(1) for m in re.finditer(r">{1,2}\|?\s*([^\s;&|<>()]+)", cmd)]
if mutates or written:
    for full, rel in paths.items():
        names = {rel, os.path.basename(rel), full}
        if any(re.search(r"(?<![\w./-])" + re.escape(n) + r"(?![\w-])", cmd if mutates else " ".join(written))
               for n in names):
            block(f"test-lock: {rel} reproduces the bug being fixed and is locked; this command would change it. "
                  "Fix the code, not the test; unlock only after the commit.")
sys.exit(0)
PY
