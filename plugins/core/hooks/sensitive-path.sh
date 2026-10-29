#!/usr/bin/env bash
# sensitive-path.sh — an edit to secrets, CI/deploy config or Claude's own settings waits for a person.
# Trigger: PreToolUse(Edit|Write|MultiEdit|NotebookEdit|Bash). Matches the target against sensitive-paths.txt
# (beside this script) plus the repo's .claude/sensitive-paths.txt, and answers `ask` so the user approves it.
# Bash counts when it writes the path (>, >>, tee, sed -i, cp/mv onto it): edit-guard lets gitignored files
# like .env through, this does not. A path named in the current ticket's plan (docs/tickets/<id>/plan.md) or
# in specs/*/PLAN.md was approved with the plan and passes. Anything unparseable passes: the rule is a prompt,
# not a sandbox. CLAUDE_SENSITIVE_PATHS=0 turns it off.
[ "${CLAUDE_SENSITIVE_PATHS:-1}" = "0" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"
LIST="$(dirname "$0")/sensitive-paths.txt"

SECRETS="$(dirname "$0")/secret-paths.txt"

HOOK_INPUT="$INPUT" LIST="$LIST" SECRETS="$SECRETS" python3 -I - <<'PY'
import fnmatch, glob, json, os, re, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
tool, ti = ev.get("tool_name", ""), ev.get("tool_input") or {}
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
top = os.path.realpath(r.stdout.strip()) if r.returncode == 0 else os.path.realpath(cwd)

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
    plans += glob.glob(os.path.join(top, "specs", "*", "PLAN.md"))
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
reason = ("sensitive-path: " + ", ".join(hits[:3]) + " is a secret, CI/deploy or Claude-config file. "
          "Approve only if you expected this change; list the path in the ticket's plan.md to pre-approve it.")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                         "permissionDecisionReason": reason}}))
sys.exit(0)
PY
