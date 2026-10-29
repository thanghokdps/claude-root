#!/usr/bin/env bash
# secret-guard.sh — a file that holds secrets stays closed: the model never reads, prints, copies or edits it.
# Trigger: PreToolUse(Read|Grep|Glob|NotebookEdit|Edit|Write|MultiEdit|Bash). Denies (permissionDecision deny)
# when a target matches secret-paths.txt (beside this script) or the repo's .claude/secret-paths.txt:
#   - file_path / notebook_path, a Grep path or glob, a Glob pattern that names a secret file
#   - Bash: a secret path as an argument of a reader/copier (cat, grep, sed, source, cp, base64 ...) or as `< file`
#   - a Grep over a directory that would search a secret file; globs, `bash -c` and `eval` strings are expanded
# Inside the repo the path is matched relative to the repo top, outside it by file name (~/.ssh/id_rsa), case-blind.
# The repo list only adds patterns (its `!` lines are ignored) and only inside the repo. Templates (.env.example) pass. Anything unparseable passes. CLAUDE_SECRET_GUARD=0 turns it off.
[ "${CLAUDE_SECRET_GUARD:-1}" = "0" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"
LIST="$(dirname "$0")/secret-paths.txt"

HOOK_INPUT="$INPUT" LIST="$LIST" python3 -I - <<'PY'
import fnmatch, glob, json, os, re, shlex, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
    tool, ti = ev.get("tool_name", ""), ev.get("tool_input") or {}
    cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    top = os.path.realpath(r.stdout.strip()) if r.returncode == 0 else os.path.realpath(cwd)
except Exception:
    sys.exit(0)

READERS = set("cat head tail less more bat strings xxd od hexdump base64 grep egrep rg ag awk sed nl tac sort uniq "
              "cut jq yq source . cp mv scp rsync open diff python python3 node ruby vi vim nvim nano emacs code view "
              "xargs dd iconv zcat gzip gunzip tar zip unzip openssl plutil security".split())
GREPS = {"grep", "egrep", "rg", "ag"}
SHELLS = {"bash", "sh", "zsh"}
WRAPPERS = {"sudo", "env", "command", "time", "nohup", "exec"}
SEPARATORS = {"&&", "||", ";", ";;", "|", "|&", "&", "(", ")"}


def read_list(f, allow_neg):
    out = []
    try:
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and (allow_neg or not line.startswith("!")):
                out.append(line)
    except OSError:
        pass
    return out


# The repo list may only add: a `!` there would let a repo (or a prompt-injected edit) re-open .env.
BUILTIN = read_list(os.environ.get("LIST", ""), True)
REPO = read_list(os.path.join(top, ".claude", "secret-paths.txt"), False)
EXEMPT = [p[1:] for p in BUILTIN if p.startswith("!")]


def match(path, pat):
    """gitignore-style: no slash matches the file name at any depth; `**/` also matches at the root. Case-blind (macOS)."""
    path, pat = path.lower(), pat.lower()
    if "/" not in pat:
        return fnmatch.fnmatchcase(os.path.basename(path), pat)
    return fnmatch.fnmatchcase(path, pat) or (pat.startswith("**/") and fnmatch.fnmatchcase(path, pat[3:]))


def is_secret(candidates, inside=True):
    hit = False
    for pat in BUILTIN + (REPO if inside else []):
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
    return is_secret([os.path.basename(full), full.lstrip(os.sep)], False)


def secret_name(name):
    """A glob or pattern that is itself the name of a secret file (.env*, *.p8, **/.env)."""
    alts = expand_braces(name, 65)
    if len(alts) > 1:
        return len(alts) > 64 or any(secret_name(a) for a in alts)
    last = name.replace("\\", "/").rstrip("/").split("/")[-1]
    if not last:
        return False
    if is_secret([last]):
        return True
    return last.lower().startswith(".env") and not any(match(last, p) for p in EXEMPT)


def expand_braces(a, limit=64):
    """Shell brace expansion ({.env,x}, {a..c} left literal) so `cat {.env,x}` is seen as `cat .env x`."""
    m = re.search(r"\{([^{}]*,[^{}]*)\}", a)
    if not m:
        return [a]
    out = []
    for alt in m.group(1).split(","):
        out += expand_braces(a[:m.start()] + alt + a[m.end():], limit)
        if len(out) >= limit:
            break
    return out[:limit]


def arg_hit(a):
    alts = expand_braces(a, 65)
    # More alternatives than we check could hide a secret past the cap: fail closed.
    return len(alts) > 64 or any(one_arg_hit(x) for x in alts)


def one_arg_hit(a):
    if re.search(r"[*?\[]", a):
        if secret_name(a):
            return True
        pattern = os.path.join(cwd, os.path.expanduser(os.path.expandvars(a)))
        return any(secret_path(m) for m in glob.glob(pattern)[:500])
    return secret_path(a)


def bash_hits(cmd, depth=0):
    if depth > 3:
        return []
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
                if redirect_in and arg_hit(t):
                    hits.append(t)
                continue
            if t and set(t) <= set("<>&|0123456789") and ("<" in t or ">" in t):
                skip, redirect_in = True, t == "<"
                continue
            args.append(t)
        redirect_in = False
        while args and (re.match(r"^\w+=", args[0]) or args[0] in WRAPPERS):
            args.pop(0)
        head = os.path.basename(args[0]) if args else ""
        if head in SHELLS:
            for i, a in enumerate(args[1:], 1):
                if re.match(r"^-[a-zA-Z]*c[a-zA-Z]*$", a) and i + 1 < len(args):
                    hits += bash_hits(args[i + 1], depth + 1)
                    break
        elif head == "eval":
            hits += bash_hits(" ".join(args[1:]), depth + 1)
        if head in READERS:
            pos = [a for a in args[1:] if not a.startswith("-")]
            # grep's first positional is the pattern (`grep ".env" README.md`), unless -e/-f supplied it.
            if os.path.basename(args[0]) in GREPS and not any(re.match(r"^(-[ef]|--regexp|--file)", a) for a in args[1:]):
                pos = pos[1:]
            hits += [a for a in pos if arg_hit(a)]
    return hits


def in_glob(f, glob_param):
    """Whether ripgrep's --glob would keep f. Braces are expanded; a `!` negation can't be judged here, so it keeps f."""
    if not glob_param or glob_param.startswith("!"):
        return True
    return any(match(os.path.basename(f), g) or match(f, g) for g in expand_braces(glob_param))


def secret_in_scope(path, glob_param):
    """First secret file a Grep over `path` (default cwd) would search, honouring .gitignore inside the repo."""
    full = os.path.realpath(os.path.join(cwd, os.path.expanduser(path or ".")))
    if not os.path.isdir(full):
        return None
    if not (full == top or full.startswith(top + os.sep)):
        # Outside the repo (~/.ssh, a sibling project) there is no .gitignore to lean on: walk it, capped.
        seen = 0
        for d, dirs, files in os.walk(full):
            dirs[:] = [x for x in dirs if x not in (".git", "node_modules")]
            for name in files:
                seen += 1
                f = os.path.join(d, name)
                if seen > 5000:
                    return full  # too big to check: fail closed, the reason asks for a narrower path
                if is_secret([name, f.lstrip(os.sep)], False) and in_glob(f, glob_param):
                    return f
        return None
    try:
        r = subprocess.run(["git", "-C", top, "ls-files", "-z", "-co", "--exclude-standard", "--",
                            os.path.relpath(full, top)], capture_output=True, text=True, timeout=5)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    for f in filter(None, r.stdout.split("\0")):
        if is_secret([f]) and in_glob(f, glob_param):
            return f
    return None


reason_extra = None
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
        if not hits:
            found = secret_in_scope(ti.get("path"), ti.get("glob"))
            if found:
                hits.append(found)
                reason_extra = (f"This search would read {found}, which holds secrets. Narrow the path to the "
                                "folder you need or add a glob that leaves it out.")
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
reason = reason_extra or reason
print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                         "permissionDecisionReason": reason}}))
sys.exit(0)
PY
