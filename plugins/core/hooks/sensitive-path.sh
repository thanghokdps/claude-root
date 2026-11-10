#!/usr/bin/env bash
# sensitive-path.sh — an edit to secrets, CI/deploy config or Claude's own settings waits for a person.
# Trigger: PreToolUse(Edit|Write|MultiEdit|NotebookEdit|Bash). Matches the target against sensitive-paths.txt
# (beside this script) plus the repo's .claude/sensitive-paths.txt, and answers `ask` so the user approves it.
# Bash counts when it writes the path (>, >>, tee, sed -i, cp/mv onto it): edit-guard lets gitignored files
# like .env through, this does not. A path named in the current ticket's plan (docs/tickets/<id>/plan.md) or
# in specs/*/PLAN.md (the repo's state dir, lib/state-dir.sh) was approved with the plan and passes. Anything unparseable passes: the rule is a prompt,
# not a sandbox. CLAUDE_SENSITIVE_PATHS=0 turns it off.
# `sensitive-path.sh post` runs on PostToolUse: an edit approved with "allow all edits during this session" (the
# mode switched to acceptEdits or auto) unlocks every path of that repo and its worktrees for the rest of the
# session until the machine reboots (the marker's name holds the boot time); a plain Yes allows that edit only.
[ "${CLAUDE_SENSITIVE_PATHS:-1}" = "0" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"
LIST="$(dirname "$0")/sensitive-paths.txt"

SECRETS="$(dirname "$0")/secret-paths.txt"

HOOK_INPUT="$INPUT" HOOK_PHASE="${1:-pre}" LIST="$LIST" SECRETS="$SECRETS" \
  STATE_LIB="$(dirname "$0")/lib/state-dir.sh" python3 -I - <<'PY'
import fnmatch, glob, hashlib, json, os, re, subprocess, sys, tempfile

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
tool, ti = ev.get("tool_name", ""), ev.get("tool_input") or {}
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
top = os.path.realpath(r.stdout.strip()) if r.returncode == 0 else os.path.realpath(cwd)


def boot_id():
    try:
        return open("/proc/sys/kernel/random/boot_id", encoding="utf-8").read().strip()
    except OSError:
        out = subprocess.run(["sysctl", "-n", "kern.boottime"], capture_output=True, text=True).stdout
        m = re.search(r"sec = (\d+)", out)
        return m.group(1) if m else ""


session, boot = ev.get("session_id") or "", boot_id()
# The shared git dir, so one approval covers the main checkout and every worktree of the repo.
common = subprocess.run(["git", "-C", top, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                        capture_output=True, text=True).stdout.strip()
repo_key = os.path.realpath(common) if common else top
unlock = None
if session and boot:
    key = hashlib.sha256("\0".join((session, boot, repo_key)).encode()).hexdigest()[:32]
    unlock = os.path.join(tempfile.gettempdir(), "claude-sensitive-path", key)
post = os.environ.get("HOOK_PHASE") == "post"
if not post and unlock and os.path.exists(unlock):
    sys.exit(0)

targets = []
if tool in ("Edit", "Write", "MultiEdit"):
    targets = [ti.get("file_path") or ""]
elif tool == "NotebookEdit":
    targets = [ti.get("notebook_path") or ""]
elif tool == "Bash":
    cmd = ti.get("command") or ""
    shell = re.sub(r"(<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n).*?\n(\s*\2\s*(?:\n|$))", r"\1\3", cmd, flags=re.S)
    shell = re.sub(r"'[^']*'|\"[^\"]*\"", "''", shell)
    targets += re.findall(r"(?<![0-9&<])>{1,2}\|?\s*([^\s;&|<>()]+)", shell)
    for seg in re.split(r"&&|\|\||[;|\n]", shell):
        words = seg.split()
        if not words:
            continue
        head, args = os.path.basename(words[0]), [w for w in words[1:] if not w.startswith("-")]
        if head == "tee":
            targets += args
        elif head in ("sed", "perl") and any(re.match(r"^-[a-zA-Z]*i", w) or w.startswith("--in-place") for w in words[1:]):
            targets += args[-1:]
        elif head in ("cp", "mv", "install", "ln") and len(args) >= 2:
            targets += args[-1:]
else:
    sys.exit(0)


def rel(path):
    path = path.strip("'\"")
    if not path or path.startswith("/dev/") or "$" in path:
        return None
    full = os.path.realpath(os.path.join(cwd, os.path.expanduser(path)))
    if not (full == top or full.startswith(top + os.sep)):
        return None
    return os.path.relpath(full, top)


def rules():
    out = []
    for f in (os.environ.get("SECRETS", ""), os.environ.get("LIST", ""),
              os.path.join(top, ".claude", "secret-paths.txt"), os.path.join(top, ".claude", "sensitive-paths.txt")):
        try:
            for line in open(f, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#"):
                    out.append(line)
        except OSError:
            pass
    return out


def match(path, pat):
    """gitignore-style: no slash matches the file name at any depth; `**/` also matches at the root."""
    if "/" not in pat:
        return fnmatch.fnmatch(os.path.basename(path), pat)
    return fnmatch.fnmatch(path, pat) or (pat.startswith("**/") and fnmatch.fnmatch(path, pat[3:]))


def sensitive(path):
    hit = False
    for pat in rules():
        if pat.startswith("!"):
            if match(path, pat[1:]):
                hit = False
        elif match(path, pat):
            hit = True
    return hit


def planned(path):
    branch = subprocess.run(["git", "-C", top, "symbolic-ref", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    m = re.match(r"^[\w.-]+/([A-Za-z]+-\d+|\d+)(?:[-_]|$)", branch)
    plans = [os.path.join(top, "docs", "tickets", m.group(1), "plan.md")] if m else []
    state = subprocess.run(["bash", "-c", '. "$1" && state_dir "$2"', "_", os.environ["STATE_LIB"], top],
                           capture_output=True, text=True).stdout.strip()
    plans += glob.glob(os.path.join(state, "specs", "*", "PLAN.md")) if state else []
    for p in plans:
        try:
            if path in open(p, encoding="utf-8").read():
                return True
        except OSError:
            pass
    return False


hits = [p for p in dict.fromkeys(filter(None, map(rel, targets))) if sensitive(p) and not planned(p)]
if not hits:
    sys.exit(0)
# A hook cannot add buttons or see which one was pressed (hooks.md: each dialog builds its own options), but the
# mode can: "Yes, allow all edits during this session" or "switch to auto mode" changes it between pre and post.
# Keyed on tool_use_id, so only the call pre actually asked about can unlock, never state the tool changed.
mode, call = ev.get("permission_mode") or "", ev.get("tool_use_id") or ""
asked = f"{unlock}.{hashlib.sha256(call.encode()).hexdigest()[:16]}.asked" if unlock and call else None
if post:
    if not asked:
        sys.exit(0)
    try:
        before = open(asked, encoding="utf-8").read()
        os.remove(asked)
    except OSError:
        sys.exit(0)
    if mode in ("acceptEdits", "auto") and mode != before:
        open(unlock, "w").close()
    sys.exit(0)
if asked:
    os.makedirs(os.path.dirname(asked), exist_ok=True)
    with open(asked, "w", encoding="utf-8") as f:
        f.write(mode)
reason = ("sensitive-path: " + ", ".join(hits[:3]) + " is a secret, CI/deploy or Claude-config file. "
          "Approve only if you expected this change; list the path in the ticket's plan.md to pre-approve it. "
          "No = deny · Yes = allow once · \"Yes, allow all edits during this session\" = allow every sensitive "
          "path of this repo for the session.")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                         "permissionDecisionReason": reason}}))
sys.exit(0)
PY
