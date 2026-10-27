#!/usr/bin/env bash
# edit-guard.sh — files in the repo change through Edit/Write, never through the shell, so the
# per-edit hooks (lint, format, blast radius) see every change.
# Trigger: PreToolUse(Bash). Blocks (exit 2) when a command run inside a git worktree:
#   - edits in place: sed -i, perl -i / -pi
#   - writes a repo file through >, >>, tee or a heredoc
#   - runs an inline python/node/ruby script (heredoc, -c, -e) that writes files
# Targets outside the worktree, gitignored paths, .git/ and /dev/* are allowed: logs, scratch files and
# build output stay possible. A script kept in a file (python3 scripts/gen.py) is allowed: it is reviewed code.
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 - <<'PY'
import json, os, re, shlex, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
if ev.get("tool_name") != "Bash":
    sys.exit(0)
cmd = (ev.get("tool_input") or {}).get("command") or ""
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
if r.returncode != 0:
    sys.exit(0)
top = os.path.realpath(r.stdout.strip())


def in_repo(path):
    """True when path is a file of the worktree that git would track."""
    path = path.strip("'\"")
    if not path or path.startswith("/dev/") or path.startswith("&") or "$" in path:
        return False
    full = os.path.realpath(os.path.join(cwd, os.path.expanduser(path)))
    if not (full == top or full.startswith(top + os.sep)):
        return False
    rel = os.path.relpath(full, top)
    if rel == ".git" or rel.startswith(".git" + os.sep):
        return False
    ignored = subprocess.run(["git", "-C", top, "check-ignore", "-q", rel], capture_output=True)
    return ignored.returncode != 0


# Heredoc bodies are data: read them only for the inline-script check, then drop them.
bodies = re.findall(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)\n\s*\1\s*(?:\n|$)", cmd, re.S)
shell = re.sub(r"(<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n).*?\n(\s*\2\s*(?:\n|$))", r"\1\3", cmd, flags=re.S)
shell = re.sub(r"'[^']*'|\"[^\"]*\"", "''", shell)  # quoted text (commit messages, grep patterns) is not a target
hits = []

for seg in re.split(r"&&|\|\||[;|\n]", shell):
    words = seg.split()
    if not words:
        continue
    head = os.path.basename(words[0])
    if head == "sed" and any(re.match(r"^-[a-zA-Z]*i", w) or w.startswith("--in-place") for w in words[1:]):
        hits.append(("sed -i", [w for w in words[1:] if not w.startswith("-")][-1:] or ["?"]))
    if head == "perl" and any(re.match(r"^-[a-zA-Z]*i", w) for w in words[1:]):
        hits.append(("perl -i", [w for w in words[1:] if not w.startswith("-")][-1:] or ["?"]))
    if head == "tee":
        hits += [("tee", [w]) for w in words[1:] if not w.startswith("-")]

for m in re.finditer(r"(?<![0-9&<])>{1,2}\|?\s*([^\s;&|<>()]+)", shell):
    hits.append(("redirect", [m.group(1)]))

blocked = [(how, t) for how, targets in hits for t in targets if t == "?" or in_repo(t)]

WRITES = r"open\([^)]*['\"][wax]\+?b?['\"]|\.write_text\(|\.write_bytes\(|writeFileSync|writeFile\(|File\.write|shutil\.(copy|move)"
inline = [b for _, b in bodies] + re.findall(r"\b(?:python3?|node|ruby)\s+-[ce]\s+(\"[^\"]*\"|'[^']*')", cmd)
if re.search(r"\b(?:python3?|node|ruby)\b", shell) and any(re.search(WRITES, b) for b in inline):
    paths = re.findall(r"['\"]([^'\"\s]+\.[A-Za-z0-9]{1,8})['\"]", " ".join(inline))
    if not paths or any(in_repo(p) for p in paths):
        blocked.append(("inline script", "a file in the repo"))

if blocked:
    print("edit-guard: change repo files with the Edit or Write tool, not the shell, so the lint and format "
          "hooks run on the change.", file=sys.stderr)
    for how, target in blocked[:5]:
        print(f"  - {how} → {target}", file=sys.stderr)
    print("Scratch output can go outside the repo or to a gitignored path; a generator belongs in a script file.",
          file=sys.stderr)
    sys.exit(2)
sys.exit(0)
PY
