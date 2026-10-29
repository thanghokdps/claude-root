#!/usr/bin/env bash
# ticket-gate.sh — a ticket's code is committed and its PR opened only after the process in its plan ran.
# Trigger: PreToolUse(Bash) on `git commit` / `gh pr create`, PreToolUse(mcp__github__create_pull_request).
# Applies on a branch <type>/<id>-<slug> whose docs/tickets/<id>/plan.md exists. It reads from plan.md:
#   Risk: high|normal
#   Skills: /agent-tool, /agent-frontend, ...      every layer skill a slice names
# and from <git-dir>/claude-ticket-ledger.jsonl (written by ticket-ledger.sh) what ran on this branch.
# Blocks (exit 2) a commit that carries code, or a PR, when:
#   - plan.md has no Skills: line or no Risk: line
#   - a listed skill never ran; /agent-verify-turn never ran though an /agent-* skill is listed
#   - no subagent ran with model sonnet or haiku (the code is written by a cheaper model)
#   - commit only: spec.md § Concerns has a `blocking` row with an empty Decision, or § Decisions has an `(agent)`
#     entry without `why:` and `revert:` (waive both: `skip concerns: <reason>`)
#   - PR only: /verify-done or /review-checklist never ran; Risk: high and /security-review or /code-review never ran
# A line `skip /<skill>: <reason>` (or `skip subagents: <reason>`) in plan.md waives one check, with the reason on record.
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

AT = r"(?:^|[;&|(]|\n)\s*(?:[A-Za-z_]\w*=\S*\s+)*"
if tool == "Bash":
    cmd = ti.get("command") or ""
    if re.search(AT + r"gh\s+pr\s+create\b", cmd):
        action = "pr"
    elif re.search(AT + r"git(?:\s+-[Cc]\s+\S+)*\s+commit\b", cmd):
        action = "commit"
    else:
        sys.exit(0)
elif tool.endswith("create_pull_request"):
    action, cmd = "pr", ""
else:
    sys.exit(0)


def git(*args):
    r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


branch = git("symbolic-ref", "--short", "HEAD")
m = re.match(r"^[\w.-]+/([A-Za-z]+-\d+|\d+)(?:[-_]|$)", branch)
top = git("rev-parse", "--show-toplevel")
if not m or not top:
    sys.exit(0)
ticket = m.group(1)
plan_path = os.path.join(top, "docs", "tickets", ticket, "plan.md")
if not os.path.exists(plan_path):
    sys.exit(0)

if action == "commit":
    files = git("diff", "--cached", "--name-only").splitlines()
    if re.search(r"\s(-a|--all|-[a-zA-Z]*a[a-zA-Z]*)\b", cmd):
        files += git("diff", "--name-only").splitlines()
    if not any(f and not f.startswith("docs/") for f in files):
        sys.exit(0)  # the contract alone, or docs: nothing to gate yet

plan = open(plan_path, encoding="utf-8").read()
waived = {w.rpartition(":")[2].lower() for w in re.findall(r"(?im)^\W*skip\s+/?([\w:-]+)\s*[:—–-]\s*\S", plan)}
risk = re.search(r"(?im)^[\s*>-]*Risk\**\s*:\**\s*`?(high|normal|low)\b", plan)
skills_line = re.search(r"(?im)^[\s*>-]*Skills\**\s*:\**\s*(.+)$", plan)
problems = []
if not skills_line:
    problems.append("plan.md has no `Skills:` line naming the layer skill of every slice")
if not risk:
    problems.append("plan.md has no `Risk: high|normal` line")
listed = [s.rpartition(":")[2].lower() for s in re.findall(r"/([\w:-]+)", skills_line.group(1))] if skills_line else []

ran, agents = set(), []
git_dir = git("rev-parse", "--absolute-git-dir")
try:
    for line in open(os.path.join(git_dir, "claude-ticket-ledger.jsonl"), encoding="utf-8"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("branch") != branch:
            continue
        if e.get("kind") == "skill":
            ran.add((e.get("name") or "").lower())
        elif e.get("kind") == "agent":
            agents.append(e)
except OSError:
    pass

need = list(listed)
if any(s.startswith("agent-") for s in listed) and "agent-verify-turn" not in need:
    need.append("agent-verify-turn")
if action == "pr":
    need += ["verify-done", "review-checklist"]
    if risk and risk.group(1).lower() == "high":
        need += ["security-review", "code-review"]
missing = [s for s in dict.fromkeys(need) if s not in ran and s not in waived]
if missing:
    problems.append("never ran on this branch: " + ", ".join("/" + s for s in missing))
cheap = [a for a in agents if re.search(r"sonnet|haiku", a.get("model") or "", re.I)]
if not cheap and "subagents" not in waived:
    problems.append("no subagent ran with model sonnet or haiku; dispatch the slice's code to one (Agent tool, model: sonnet)")

spec_path = os.path.join(top, "docs", "tickets", ticket, "spec.md")
if action == "commit" and "concerns" not in waived and os.path.exists(spec_path):
    in_concerns = False
    for line in open(spec_path, encoding="utf-8").read().splitlines():
        if re.match(r"^#{1,6}\s", line):
            in_concerns = bool(re.match(r"^#{1,6}\s+Concerns\b", line, re.I))
            continue
        if not in_concerns or not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6 or re.sub(r"[*`\s]", "", cells[2]).lower() != "blocking":
            continue
        if re.sub(r"[*`\s]", "", cells[-1]) in ("", "—", "-", "–"):
            problems.append(f"{cells[0] or 'a concern'} is blocking and has no decision (spec.md § Concerns)")
    in_decisions = False
    for line in open(spec_path, encoding="utf-8").read().splitlines():
        if re.match(r"^#{1,6}\s", line):
            in_decisions = bool(re.match(r"^#{1,6}\s+Decisions\b", line, re.I))
            continue
        entry = re.match(r"^\s*[-*]\s+(.+)$", line)
        if not in_decisions or not entry or not re.search(r"\(agent\)", entry.group(1), re.I):
            continue
        if not (re.search(r"\bwhy\s*:", line, re.I) and re.search(r"\brevert\s*:", line, re.I)):
            problems.append(f"decision by agent has no why:/revert: “{entry.group(1)[:60]}” (spec.md § Decisions)")

if problems:
    what = "commit" if action == "commit" else "open the PR"
    print(f"ticket-gate: cannot {what} for ticket {ticket} yet —", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    print(f"Run what is missing, or record a waiver in docs/tickets/{ticket}/plan.md as `skip /<skill>: <reason>` "
          "(`skip subagents: <reason>`), then retry.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
PY
