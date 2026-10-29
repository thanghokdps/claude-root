#!/usr/bin/env bash
# weakened-check.sh — a commit that lowers the bar asks the user first.
# Trigger: PreToolUse(Bash), only for git commit. Reads the staged diff (git diff HEAD for commit -a) and asks on:
#   - an added suppression (eslint-disable, @ts-ignore, # noqa, …) or skip (.skip(, .only(, xit(, t.Skip(, …)
#   - a deleted test file, or a kept test file that loses more assertion lines than it gains
#   - coverageThreshold / fail_under / --cov-fail-under lowered, max-warnings raised
# Tightening is silent. Diff walk ported from addyosmani/agent-skills constraint-driven-development floor-guard.md.
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 -I - <<'PY'
import json, os, re, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
if ev.get("tool_name") != "Bash":
    sys.exit(0)
cmd = (ev.get("tool_input") or {}).get("command") or ""
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

AT = r"(?:^|[;&|(]|\n)\s*(?:[A-Za-z_]\w*=\S*\s+)*"
m = re.search(AT + r"git((?:\s+(?:-[Cc]\s+\S+|--\S+))*)\s+commit\b([^;&|\n]*)", cmd)
if not m:
    sys.exit(0)
for d in re.findall(r"-C\s+(\S+)", m.group(1)):
    cwd = os.path.join(cwd, os.path.expanduser(d.strip("'\"")))
commit_all = re.search(r"\s(?:--all\b|-[A-Za-z]*a)", m.group(2))


def git(*args):
    # Runs before the user approves, so a repo's own config must not get to run a command (fsmonitor, textconv).
    r = subprocess.run(["git", "-C", cwd, "-c", "core.fsmonitor=false", *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


if not git("rev-parse", "--show-toplevel"):
    sys.exit(0)
diff = git("diff", "HEAD" if commit_all else "--cached", "-U0", "--no-color", "--no-ext-diff", "--no-textconv")
if not diff:
    sys.exit(0)

# `---`/`+++` are headers only between a file's `diff` line and its first `@@`; inside a hunk they are content.
added, removed, deleted = [], [], set()
file = old_file = ""
in_header, old_no, new_no = False, 0, 0
for line in diff.split("\n"):
    if line.startswith("diff "):
        in_header = True
    elif line.startswith("@@"):
        in_header = False
        h = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)", line)
        old_no, new_no = (int(h.group(1)), int(h.group(2))) if h else (0, 0)
    elif in_header:
        if line.startswith("--- "):
            old_file = re.sub(r"^[ab]/", "", line[4:])
        elif line.startswith("+++ "):
            new_file = re.sub(r"^[ab]/", "", line[4:])
            file = old_file if new_file == "/dev/null" else new_file
            if new_file == "/dev/null":
                deleted.add(file)
    elif line.startswith("+"):
        added.append((file, new_no, line[1:]))
        new_no += 1
    elif line.startswith("-"):
        removed.append((file, old_no, line[1:]))
        old_no += 1

findings = []


def flag(rule, f, n, text):
    text = re.sub(r"[A-Za-z0-9_+/=-]{20,}", "<redacted>", text.strip())  # tokens, keys, hashes
    findings.append(f"[{rule}] {f}{f':{n}' if n else ''} {text[:80] + '…' if len(text) > 80 else text}")


def is_test(f):
    return bool(re.search(r"\.(test|spec)\.|_test\.|^test_", os.path.basename(f)))


SUPPRESSIONS = re.compile(r"eslint-disable|@ts-ignore|@ts-nocheck|@ts-expect-error|biome-ignore|#\s*noqa"
                          r"|#\s*type:\s*ignore|istanbul ignore|nosemgrep")
SKIPS = re.compile(r"\.(?:skip|only)\(|\bxit\(|\bxdescribe\(|@pytest\.mark\.skip|\bt\.Skip\(")
ASSERT = re.compile(r"\b(?:expect|assert|should)\b")
# (key, value) per threshold; a floor is loosened by going down, a ceiling by going up.
THRESHOLDS = [(re.compile(r"coverageThreshold\b.*?(\d+(?:\.\d+)?)"), "floor"),
              (re.compile(r"\bfail_under\b\D*?(\d+(?:\.\d+)?)"), "floor"),
              (re.compile(r"--cov-fail-under\D*?(\d+(?:\.\d+)?)"), "floor"),
              (re.compile(r"max-warnings\D*?(\d+)"), "ceiling")]

for f, n, text in added:
    if SUPPRESSIONS.search(text):
        flag("suppression", f, n, text)
    if SKIPS.search(text):
        flag("skip", f, n, text)

for f in sorted(deleted):
    if is_test(f):
        flag("test-deleted", f, 0, "file deleted")

# A rewritten assertion is a removed/added pair; only a net loss in a kept test file asks.
for f in {f for f, _, _ in removed if is_test(f) and f not in deleted}:
    gone = [(n, t) for g, n, t in removed if g == f and ASSERT.search(t)]
    if len(gone) > sum(1 for g, _, t in added if g == f and ASSERT.search(t)):
        for n, t in gone:
            flag("assertion-removed", f, n, t)

for key, kind in THRESHOLDS:
    for f, n, text in removed:
        was = key.search(text)
        now = next((key.search(t) for g, _, t in added if g == f and key.search(t)), None)
        if was and now:
            a, b = float(was.group(1)), float(now.group(1))
            if (b < a) if kind == "floor" else (b > a):
                flag("threshold-loosened", f, n, f"{was.group(1)} -> {now.group(1)}: {text}")

if findings:
    shown = findings[:10] + ([f"… and {len(findings) - 10} more"] if len(findings) > 10 else [])
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "ask",
        "permissionDecisionReason": "weakened-check: this commit lowers the bar:\n" + "\n".join(shown)
        + "\nApprove only if each one is intended; otherwise fix the code instead."}}))
sys.exit(0)
PY
