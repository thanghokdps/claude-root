#!/usr/bin/env python3
"""Settle the decisions agents made for the user against what git did with them afterwards.

Reads every agent decision committed in docs/tickets/<id>/plan.md (§ Auto decisions) and
spec.md (`(agent)` lines), finds the commit that recorded it, and looks at the later commits
on the files its `revert:` names:
  reverted  a later commit's subject starts with "revert"
  changed   a later commit's subject starts with "fix"
  kept      neither, and the decision is at least --min-days old
  pending   neither, and it is younger: too early to judge
Decisions whose key is already in .claude/docs/decisions.md are skipped (settled before).
Prints one JSON object per line. Usage: settle-decisions.py [repo] [--min-days N] [--all]
(--all also prints pending ones). Read-only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

LEDGER = os.path.join(".claude", "docs", "decisions.md")
PATH_RE = re.compile(r"[\w.@-]+(?:/[\w.@-]+)+|[\w-]+\.[A-Za-z]{1,5}\b")


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


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


def settle(repo, ticket, rel, decision, min_days, now):
    head = decision.split(" · ")[0].strip()
    key = f"[{ticket}] {head}"
    first = git(repo, "log", "--reverse", "--format=%H %ct", "-S", decision[:120], "--", rel).splitlines()
    if not first:
        return None
    sha, when = first[0].split()
    row = {"ticket": ticket, "file": rel, "key": key, "decision": decision, "since": sha[:7], "evidence": []}
    paths = revert_paths(repo, decision)
    if not paths:
        return {**row, "status": "unreadable", "why": "revert: names no file in the repo"}
    # shortcut: commits that also touch the ticket's own docs count as its build, not a later
    # change; a squash merge keeps it right, a ticket fixed later without its docs is missed.
    own = f"docs/tickets/{ticket}/"
    log = git(repo, "log", "--format=%x1e%H%x09%s", "--name-only", f"{sha}..HEAD", "--", *paths, own)
    status = None
    for block in log.split("\x1e"):
        lines = [x for x in block.splitlines() if x.strip()]
        if not lines or "\t" not in lines[0]:
            continue
        csha, subject = lines[0].split("\t", 1)
        if any(f.startswith(own) for f in lines[1:]):
            continue
        kind = "reverted" if re.match(r"(?i)revert\b", subject) else "changed" if re.match(r"(?i)fix\b", subject) else None
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
    for rel in git(top, "ls-files", "docs/tickets/*/plan.md", "docs/tickets/*/spec.md").splitlines():
        ticket = rel.split("/")[2]
        text = open(os.path.join(top, rel), encoding="utf-8").read()
        for decision in decision_lines(text, os.path.basename(rel)):
            row = settle(top, ticket, rel, decision, opts.min_days, now)
            if not row or row["key"] in settled:
                continue
            if row["status"] != "pending" or opts.all:
                print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
