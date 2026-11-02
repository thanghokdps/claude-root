#!/usr/bin/env python3
"""Tests for plugins/core/scripts/sync-team.sh. Run: python3 scripts/test_sync_team.py"""
import datetime
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "core", "scripts", "sync-team.sh")


def git(path, *a, user="me"):
    return subprocess.run(["git", "-C", path, "-c", f"user.name={user}", "-c", f"user.email={user}@t", *a],
                          check=True, capture_output=True, text=True).stdout.strip()


def repo(configure_user=True):
    d = tempfile.mkdtemp(prefix="sync-team-")
    git(d, "init", "-q", "-b", "main")
    if configure_user:
        git(d, "config", "user.name", "me")
        git(d, "config", "user.email", "me@t")
    return d


def commit(d, name, user="me"):
    with open(os.path.join(d, name), "w") as f:
        f.write(name)
    git(d, "add", name)
    git(d, "commit", "-q", "-m", f"add {name}", user=user)


def sync(d):
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    return subprocess.run(["bash", SCRIPT, d], capture_output=True, text=True, env=env)


def day_file(d):
    return os.path.join(d, ".claude", "memory", "commits", datetime.date.today().isoformat() + ".md")


def test_writes_my_commits_and_last_sync():
    d = repo()
    commit(d, "a.txt")
    commit(d, "b.txt", user="mate")
    p = sync(d)
    assert p.returncode == 0, p.stdout + p.stderr
    text = open(day_file(d)).read()
    mine = text.partition("# Team changes")[0]
    assert "**add a.txt**" in mine and "**add b.txt**" not in mine, text
    head_mine = git(d, "log", "--author=me", "-1", "--format=%H")
    assert open(os.path.join(d, ".claude", "memory", "commits", "last-sync.txt")).read().strip() == head_mine


def test_memory_index_gets_one_entry_per_day():
    d = repo()
    commit(d, "a.txt")
    os.makedirs(os.path.join(d, ".claude", "memory"))
    open(os.path.join(d, ".claude", "memory", "MEMORY.md"), "w").write("# Memory\n")
    assert sync(d).returncode == 0
    idx = open(os.path.join(d, ".claude", "memory", "MEMORY.md")).read()
    assert idx.count("Commits " + datetime.date.today().isoformat()) == 1, idx


def test_second_run_without_index_is_a_noop_success():
    d = repo()
    commit(d, "a.txt")
    sync(d)
    sync_file = os.path.join(d, ".claude", "memory", "commits", "last-sync.txt")
    before = open(sync_file).read()
    p = sync(d)
    assert p.returncode == 0 and "No new commits from you" in p.stdout, p.stdout + p.stderr
    assert open(sync_file).read() == before


def test_rerun_with_index_and_no_new_commits_exits_zero():
    d = repo()
    commit(d, "a.txt")
    os.makedirs(os.path.join(d, ".claude", "memory"))
    open(os.path.join(d, ".claude", "memory", "MEMORY.md"), "w").write("# Memory\n")
    assert sync(d).returncode == 0
    p = sync(d)
    assert p.returncode == 0, p.stdout + p.stderr


def test_same_day_rerun_appends_without_duplicates():
    d = repo()
    commit(d, "a.txt")
    commit(d, "b.txt")
    assert sync(d).returncode == 0
    commit(d, "c.txt")
    p = sync(d)
    assert p.returncode == 0, p.stdout + p.stderr
    text = open(day_file(d)).read()
    for n in ("a.txt", "b.txt", "c.txt"):
        assert text.count(f"**add {n}**") == 1, text
    assert text.count("name: commits-") == 1, text


def test_team_section_lists_mate_not_me():
    d = repo()
    commit(d, "a.txt")
    commit(d, "b.txt", user="mate")
    assert sync(d).returncode == 0
    team = open(day_file(d)).read().partition("# Team changes")[2]
    assert "add b.txt" in team and "[mate]" in team and "add a.txt" not in team, team


def test_missing_git_user_fails_with_a_clear_line():
    d = repo(configure_user=False)
    p = sync(d)
    assert p.returncode != 0 and "No git user.name configured" in p.stdout, (p.returncode, p.stdout)


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    for name, t in tests:
        t()
        print(f"ok {name}")
    print(f"test_sync_team: {len(tests)} passed")
