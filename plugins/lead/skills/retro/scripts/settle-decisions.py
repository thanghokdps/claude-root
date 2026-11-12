#!/usr/bin/env python3
"""Settle the decisions agents made for the user against what git did with them afterwards.

Reads every agent decision in a ticket's contract, specs/<id>-<slug>/plan.md (§ Auto decisions) and
spec.md (`(agent)` lines) in the repo's personal state dir (never committed), finds the ticket's
first commit (subject ending `(#<id>)`), and looks at the later commits on the files its `revert:` names:
  reverted  a later commit's subject starts with "revert"
  changed   a later commit's subject starts with "fix"
  kept      neither, and the decision is at least --min-days old
  pending   neither, and it is younger: too early to judge
Decisions whose key is already in .claude/docs/decisions.md are skipped (settled before).
Prints one JSON object per line. Usage: settle-decisions.py [repo] [--min-days N] [--all]
(--all also prints pending ones). Read-only.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

LEDGER = os.path.join(".claude", "docs", "decisions.md")
PATH_RE = re.compile(r"[\w.@-]+(?:/[\w.@-]+)+|[\w-]+\.[A-Za-z]{1,5}\b")
TICKET_RE = re.compile(r"^([A-Za-z]+-\d+|\d+)(?:[-_]|$)")


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def specs_dir(repo):
    """<state>/specs: the same path as core's hooks/lib/state-dir.sh, keyed by the resolved git common dir."""
    real = os.path.realpath(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    data = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    name = os.path.basename(os.path.dirname(real)) + "-" + hashlib.sha1(real.encode()).hexdigest()[:8]
    return os.path.join(data, "claude-harness", "repos", name, "specs")


def contracts(specs):
    """(ticket id, path) of every plan.md / spec.md in a ticket's contract folder."""
    try:
        folders = sorted(os.listdir(specs))
    except OSError:
        return []
    found = []
    for folder in folders:
        m = TICKET_RE.match(folder)
        if not m or not os.path.isdir(os.path.join(specs, folder)):
            continue
        names = os.listdir(os.path.join(specs, folder))  # exact case: a feature's PLAN.md is not a contract
        found += [(m.group(1), os.path.join(specs, folder, n)) for n in ("plan.md", "spec.md") if n in names]
    return found


def decision_lines(text, name):
    """Bullet lines that are agent decisions: § Auto decisions entries, or `(agent)` lines."""
    section = re.search(r"(?ims)^##\s+Auto decisions\s*$(.*?)(?=^##\s|\Z)", text)
    found = re.findall(r"(?m)^\s*[-*]\s+(.+)$", section.group(1)) if section and name == "plan.md" else []
    found += [line for line in re.findall(r"(?m)^\s*[-*]\s+(.+)$", text) if "(agent)" in line]
    return [d.strip() for d in dict.fromkeys(found) if "revert:" in d and not re.match(r"(?i)none\b", d)]


def revert_paths(repo, decision):
    """Repo paths named in the `revert:` part; a partial path matches any file ending in it."""
    tail = decision.split("revert:", 1)[1]
    paths = []
    for token in PATH_RE.findall(tail):
        token = token.strip("./")
        if git(repo, "log", "-1", "--format=%H", "--", f":(glob)**/{token}"):
            paths.append(f":(glob)**/{token}")
    return paths


def settle(repo, ticket, path, decision, min_days, now):
    head = decision.split(" · ")[0].strip()
    key = f"[{ticket}] {head}"
    own = f"(#{ticket})"
    first = git(repo, "log", "--reverse", "--format=%H %ct", "--fixed-strings", f"--grep={own}").splitlines()
    if not first:
        return None  # the ticket has no commit yet: nothing to settle against
    sha, when = first[0].split()
    row = {"ticket": ticket, "file": path, "key": key, "decision": decision, "since": sha[:7], "evidence": []}
    paths = revert_paths(repo, decision)
    if not paths:
        return {**row, "status": "unreadable", "why": "revert: names no file in the repo"}
    # shortcut: commits whose subject carries the ticket's `(#<id>)` count as its build, not a later
    # change; a squash merge keeps it right, a later fix that reuses the ticket's tag is missed.
    log = git(repo, "log", "--format=%x1e%H%x09%s", f"{sha}..HEAD", "--", *paths)
    status = None
    for block in log.split("\x1e"):
        lines = [x for x in block.splitlines() if x.strip()]
        if not lines or "\t" not in lines[0]:
            continue
        csha, subject = lines[0].split("\t", 1)
        reverted = re.match(r"(?i)revert\b", subject)  # git revert keeps the reverted subject, `(#<id>)` included
        if own in subject and not reverted:
            continue
        kind = "reverted" if reverted else "changed" if re.match(r"(?i)fix\b", subject) else None
        if kind:
            row["evidence"].append({"sha": csha[:7], "subject": subject})
            status = "reverted" if "reverted" in (status, kind) else kind
    if status:
        return {**row, "status": status}
    age_days = (now - int(when)) / 86400
    return {**row, "status": "kept" if age_days >= min_days else "pending"}


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("repo", nargs="?", default=".")
    p.add_argument("--min-days", type=int, default=14)
    p.add_argument("--all", action="store_true")
    opts = p.parse_args(argv)
    top = git(os.path.abspath(opts.repo), "rev-parse", "--show-toplevel")
    if not top:
        print("settle-decisions: not a git repository", file=sys.stderr)
        return 2
    try:
        settled = open(os.path.join(top, LEDGER), encoding="utf-8").read()
    except OSError:
        settled = ""
    now = int(time.time())
    for ticket, path in contracts(specs_dir(top)):
        text = open(path, encoding="utf-8").read()
        for decision in decision_lines(text, os.path.basename(path)):
            row = settle(top, ticket, path, decision, opts.min_days, now)
            if not row or f" · {row['key']} · " in settled:
                continue
            if row["status"] != "pending" or opts.all:
                print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
