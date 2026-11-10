#!/usr/bin/env python3
"""Tests for plugins/core/scripts/sync-team.sh. Run: python3 scripts/test_sync_team.py"""
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


def commit(d, name, user="me", content=None):
    with open(os.path.join(d, name), "w") as f:
        f.write(content or name)
    git(d, "add", name)
    git(d, "commit", "-q", "-m", f"add {name} by {user}", user=user)


def sync(d):
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull}
    return subprocess.run(["bash", SCRIPT, d], capture_output=True, text=True, env=env)


def section(out, title):
    return out.partition(title)[2].partition("\n\n")[0]


def test_splits_my_commits_from_the_team():
    d = repo()
    commit(d, "a.txt")
    commit(d, "b.txt", user="mate")
    p = sync(d)
    assert p.returncode == 0, p.stdout + p.stderr
    yours, team = p.stdout.partition("Team (")[0], p.stdout.partition("Team (")[2]
    assert "add a.txt by me" in yours and "add b.txt" not in yours, p.stdout
    assert "[mate] add b.txt by mate" in team and "add a.txt" not in team, p.stdout


def test_writes_nothing_into_the_repo():
    d = repo()
    commit(d, "a.txt")
    assert sync(d).returncode == 0
    assert not os.path.exists(os.path.join(d, ".claude")), os.listdir(d)
    assert git(d, "status", "--porcelain") == ""


def test_flags_a_file_both_of_us_changed():
    d = repo()
    commit(d, "shared.txt")
    commit(d, "shared.txt", user="mate", content="theirs")
    p = sync(d)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "Re-check" in p.stdout and "- shared.txt" in p.stdout, p.stdout


def test_no_overlap_section_without_shared_files():
    d = repo()
    commit(d, "a.txt")
    commit(d, "b.txt", user="mate")
    assert "Re-check" not in sync(d).stdout


def test_lists_only_what_the_pull_brought_in():
    upstream = repo()
    commit(upstream, "old.txt", user="mate")
    d = tempfile.mkdtemp(prefix="sync-clone-")
    subprocess.run(["git", "clone", "-q", upstream, d], check=True, capture_output=True)
    git(d, "config", "user.name", "me")
    commit(upstream, "new.txt", user="mate")
    p = sync(d)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "Commits the pull brought in" in p.stdout and "add new.txt" in p.stdout, p.stdout
    assert "add old.txt" not in p.stdout, p.stdout


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
