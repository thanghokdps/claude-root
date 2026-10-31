#!/usr/bin/env python3
"""Tests for plugins/lead/skills/retro/scripts/settle-decisions.py. Run: python3 scripts/test_settle_decisions.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "lead", "skills", "retro", "scripts", "settle-decisions.py")

PLAN = """# Plan
Risk: high

## Auto decisions
- Rename write path · options: PATCH route / interrupt · chose the route · challenged: audit row → kept · revert: move the write into src/tools/rename.ts
- Cache key · options: user id / session id · chose user id · challenged: shared devices → kept · revert: key by session in src/cache.ts
- Page size · options: 20 / 50 · chose 20 · challenged: fewer requests → kept · revert: change PAGE in lib/page.ts
- none: the rest were the user's

## Steps
- [x] build it · revert: nothing (not a decision)
"""
SPEC = """# Spec
## Decisions
- 2026-10-01 Retry count → 3 (agent) · why: matches http.ts · revert: set RETRIES in src/http.ts
- 2026-10-01 Locale → vi (user)
"""


def git(path, *a):
    return subprocess.run(["git", "-C", path, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                          check=True, capture_output=True, text=True).stdout.strip()


def write(repo, rel, text):
    path = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def commit(repo, msg, *files):
    for rel in files:
        write(repo, rel, msg + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)


def setup():
    repo = tempfile.mkdtemp(prefix="settle-")
    git(repo, "init", "-q", "-b", "main")
    write(repo, "docs/tickets/412/plan.md", PLAN)
    write(repo, "docs/tickets/412/spec.md", SPEC)
    commit(repo, "feat: 412 build", "src/tools/rename.ts", "src/cache.ts", "lib/page.ts", "src/http.ts")
    return repo


def run(repo, *extra):
    p = subprocess.run(["python3", "-I", SCRIPT, repo, *extra], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    return {json.loads(line)["key"]: json.loads(line) for line in p.stdout.splitlines()}


def test_young_decisions_stay_pending_and_are_hidden():
    repo = setup()
    assert run(repo) == {}
    rows = run(repo, "--all")
    assert {r["status"] for r in rows.values()} == {"pending"}, rows
    assert set(rows) == {"[412] Rename write path", "[412] Cache key", "[412] Page size",
                         "[412] 2026-10-01 Retry count → 3 (agent)"}, rows


def test_later_revert_and_fix_settle_the_decision():
    repo = setup()
    commit(repo, "Revert \"feat: rename via route\"", "src/tools/rename.ts")
    commit(repo, "fix: cache by session", "src/cache.ts")
    commit(repo, "feat: unrelated", "lib/page.ts")
    rows = run(repo, "--min-days", "0")
    assert rows["[412] Rename write path"]["status"] == "reverted", rows
    assert rows["[412] Cache key"]["evidence"][0]["subject"] == "fix: cache by session", rows
    assert rows["[412] Cache key"]["status"] == "changed"
    assert rows["[412] Page size"]["status"] == "kept"
    assert rows["[412] 2026-10-01 Retry count → 3 (agent)"]["status"] == "kept"


def test_commit_inside_the_ticket_is_its_build_not_a_change():
    repo = setup()
    write(repo, "docs/tickets/412/plan.md", PLAN + "\n- [x] fix review comment\n")
    commit(repo, "fix: 412 review comment", "src/cache.ts")
    assert run(repo, "--min-days", "0")["[412] Cache key"]["status"] == "kept"


def test_settled_keys_in_the_ledger_are_skipped():
    repo = setup()
    write(repo, ".claude/docs/decisions.md", "- 2026-10-31 · kept · [412] Page size · lesson: none\n")
    commit(repo, "docs: ledger")
    assert "[412] Page size" not in run(repo, "--min-days", "0")


def test_a_longer_settled_key_does_not_hide_a_shorter_one():
    repo = setup()
    write(repo, ".claude/docs/decisions.md", "- 2026-10-31 · kept · [412] Page size limit · lesson: none\n")
    commit(repo, "docs: ledger")
    assert "[412] Page size" in run(repo, "--min-days", "0")


def test_revert_naming_no_file_is_unreadable():
    repo = setup()
    write(repo, "docs/tickets/9/plan.md", "## Auto decisions\n- Tone · chose terse · challenged: x · revert: be chatty\n")
    commit(repo, "docs: 9")
    assert run(repo, "--all")["[9] Tone"]["status"] == "unreadable"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
