#!/usr/bin/env bash
# secret-guard.sh — a file that holds secrets stays closed: the model never reads, prints, copies or edits it.
# Trigger: PreToolUse(Read|Grep|Glob|NotebookEdit|Edit|Write|MultiEdit|Bash). Denies (permissionDecision deny)
# when a target matches secret-paths.txt (beside this script) or the repo's .claude/secret-paths.txt:
#   - file_path / notebook_path, a Grep path or glob, a Glob pattern that names a secret file
#   - Bash: a secret path as an argument of a reader/copier (cat, grep, sed, source, cp, base64 ...) or as `< file`
# Inside the repo the path is matched relative to the repo top, outside it by file name (~/.ssh/id_rsa).
# Templates (.env.example) pass. Anything unparseable passes. CLAUDE_SECRET_GUARD=0 turns it off.
[ "${CLAUDE_SECRET_GUARD:-1}" = "0" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"
LIST="$(dirname "$0")/secret-paths.txt"

HOOK_INPUT="$INPUT" LIST="$LIST" python3 - <<'PY'
import fnmatch, json, os, re, shlex, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
    tool, ti = ev.get("tool_name", ""), ev.get("tool_input") or {}
    cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    top = os.path.realpath(r.stdout.strip()) if r.returncode == 0 else os.path.realpath(cwd)
except Exception:
    sys.exit(0)

READERS = set("cat head tail less more bat strings xxd od hexdump base64 grep egrep rg ag awk sed nl tac sort uniq "
              "cut jq yq source . cp mv scp rsync open diff python python3 node ruby".split())
GREPS = {"grep", "egrep", "rg", "ag"}
WRAPPERS = {"sudo", "env", "command", "time", "nohup", "exec"}
SEPARATORS = {"&&", "||", ";", ";;", "|", "|&", "&", "(", ")"}


def rules():
    out = []
    for f in (os.environ.get("LIST", ""), os.path.join(top, ".claude", "secret-paths.txt")):
        try:
            for line in open(f, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#"):
                    out.append(line)
        except OSError:
            pass
    return out


RULES = rules()


def match(path, pat):
    """gitignore-style: no slash matches the file name at any depth; `**/` also matches at the root."""
    if "/" not in pat:
        return fnmatch.fnmatch(os.path.basename(path), pat)
    return fnmatch.fnmatch(path, pat) or (pat.startswith("**/") and fnmatch.fnmatch(path, pat[3:]))


def is_secret(candidates):
    hit = False
    for pat in RULES:
        neg = pat.startswith("!")
        if any(match(c, pat[1:] if neg else pat) for c in candidates):
            hit = not neg
    return hit


def secret_path(path):
    path = (path or "").strip()
    if not path or path.startswith("/dev/") or "$(" in path:
        return False
    full = os.path.realpath(os.path.join(cwd, os.path.expandvars(os.path.expanduser(path))))
    if full == top or full.startswith(top + os.sep):
        return is_secret([os.path.relpath(full, top)])
    return is_secret([os.path.basename(full), full.lstrip(os.sep)])


def secret_name(name):
    """A glob or pattern that is itself the name of a secret file (.env*, *.p8, **/.env)."""
    last = name.replace("\\", "/").rstrip("/").split("/")[-1]
    if not last:
        return False
    if is_secret([last]):
        return True
    exempt = any(p.startswith("!") and match(last, p[1:]) for p in RULES)
    return last.startswith(".env") and not exempt


def bash_hits(cmd):
    cmd = re.sub(r"(<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n).*?\n(\s*\2\s*(?:\n|$))", r"\1\3", cmd, flags=re.S)
    cmd = cmd.replace("`", " ; ").replace("\n", " ; ")
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        toks = list(lex)
    except ValueError:
        toks = [t.strip("'\"") for t in re.split(r"\s+|&&|\|\||[;|()]", cmd) if t]
    segs, cur = [], []
    for t in toks:
        if t in SEPARATORS:
            segs.append(cur)
            cur = []
        else:
            cur.append(t)
    segs.append(cur)

    hits = []
    for seg in segs:
        args, redirect_in, skip = [], False, False
        for t in seg:
            if skip:
                skip = False
                if redirect_in and secret_path(t):
                    hits.append(t)
                continue
            if t and set(t) <= set("<>&|0123456789") and ("<" in t or ">" in t):
                skip, redirect_in = True, t == "<"
                continue
            args.append(t)
        redirect_in = False
        while args and (re.match(r"^\w+=", args[0]) or args[0] in WRAPPERS):
            args.pop(0)
        if args and os.path.basename(args[0]) in READERS:
            pos = [a for a in args[1:] if not a.startswith("-")]
            # grep's first positional is the pattern (`grep ".env" README.md`), unless -e/-f supplied it.
            if os.path.basename(args[0]) in GREPS and not any(re.match(r"^(-[ef]|--regexp|--file)", a) for a in args[1:]):
                pos = pos[1:]
            hits += [a for a in pos if secret_path(a)]
    return hits


try:
    hits = []
    if tool in ("Read", "Edit", "Write", "MultiEdit"):
        hits = [ti.get("file_path")] if secret_path(ti.get("file_path")) else []
    elif tool == "NotebookEdit":
        hits = [ti.get("notebook_path")] if secret_path(ti.get("notebook_path")) else []
    elif tool == "Grep":
        if secret_path(ti.get("path")):
            hits.append(ti.get("path"))
        if ti.get("glob") and secret_name(ti["glob"]):
            hits.append(ti["glob"])
    elif tool == "Glob":
        pat = ti.get("pattern") or ""
        if secret_name(pat) or (not re.search(r"[*?\[{]", pat) and secret_path(pat)):
            hits.append(pat)
        if secret_path(ti.get("path")):
            hits.append(ti.get("path"))
    elif tool == "Bash":
        hits = bash_hits(ti.get("command") or "")
except Exception:
    sys.exit(0)

if not hits:
    sys.exit(0)
reason = (f"{hits[0]} holds secrets, so it stays closed: never read, print, copy or edit it. Ask the developer "
          "for the value you need, use the committed template (.env.example) for variable names, and refer to "
          "credential files by path only. CLAUDE_SECRET_GUARD=0 turns this off for a session.")
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                         "permissionDecisionReason": reason}}))
sys.exit(0)
PY
