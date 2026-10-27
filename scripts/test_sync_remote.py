#!/usr/bin/env python3
"""Tests for plugins/ship/skills/sync-remote/scripts/sync-remote.sh. Run: python3 scripts/test_sync_remote.py"""
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "ship", "skills", "sync-remote", "scripts", "sync-remote.sh")


def git(path, *a):
    return subprocess.run(["git", "-C", path, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                          check=True, capture_output=True, text=True).stdout.strip()


def setup():
    """A work repo with remotes `origin` (…/github.com/app.git) and `lab` (…/gitlab.com/app.git), both at one commit on main."""
    base = tempfile.mkdtemp(prefix="sync-remote-")
    hub, lab = os.path.join(base, "github.com", "app.git"), os.path.join(base, "gitlab.com", "app.git")
    for bare in (hub, lab):
        os.makedirs(bare)
        git(bare, "init", "-q", "--bare", "-b", "main")
    work = os.path.join(base, "work")
    git(base, "init", "-q", "-b", "main", work)
    git(work, "commit", "-q", "--allow-empty", "-m", "init")
    git(work, "remote", "add", "origin", hub)
    git(work, "remote", "add", "lab", lab)
    git(work, "push", "-q", "origin", "main")
    git(work, "push", "-q", "lab", "main")
    return work


def plan(work, *extra):
    p = subprocess.run(["bash", SCRIPT, work, *extra], capture_output=True, text=True)
    rows = [line.split("\t") for line in p.stdout.splitlines()]
    return p.returncode, {r[1]: r for r in rows if r[0] != "remotes"}


def commit_and_push(work, branch, remote):
    git(work, "checkout", "-q", "-B", branch)
    git(work, "commit", "-q", "--allow-empty", "-m", branch)
    git(work, "push", "-q", remote, branch)


def test_in_sync_is_same():
    code, rows = plan(setup())
    assert code == 0 and rows["main"][0] == "same", rows


def test_branch_only_on_github_is_pushed_to_gitlab():
    work = setup()
    commit_and_push(work, "feat/a", "origin")
    _, rows = plan(work)
    kind, _, detail, cmd = rows["feat/a"]
    assert kind == "push" and "only on origin" in detail, rows
    assert cmd.endswith("push lab refs/sync-remote/origin/heads/feat/a:refs/heads/feat/a"), cmd
    subprocess.run(cmd, shell=True, check=True, capture_output=True)
    assert plan(work)[1]["feat/a"][0] == "same"


def test_ahead_side_fast_forwards_the_other():
    work = setup()
    commit_and_push(work, "feat/b", "origin")
    git(work, "push", "-q", "lab", "feat/b")
    git(work, "commit", "-q", "--allow-empty", "-m", "more")
    git(work, "push", "-q", "lab", "feat/b")
    kind, _, detail, cmd = plan(work)[1]["feat/b"]
    assert kind == "push" and "lab ahead of origin by 1" in detail and " push origin " in cmd, (kind, detail, cmd)


def test_diverged_branch_is_never_pushed():
    work = setup()
    commit_and_push(work, "feat/c", "origin")
    git(work, "reset", "-q", "--hard", "HEAD~1")
    git(work, "commit", "-q", "--allow-empty", "-m", "other side")
    git(work, "push", "-q", "lab", "feat/c")
    kind, _, _, cmd = plan(work)[1]["feat/c"]
    assert kind == "diverged" and cmd == "", (kind, cmd)


def test_main_and_env_branches_are_left_to_the_user():
    work = setup()
    git(work, "checkout", "-q", "main")
    git(work, "commit", "-q", "--allow-empty", "-m", "on main")
    git(work, "push", "-q", "origin", "main")
    commit_and_push(work, "staging", "origin")
    _, rows = plan(work)
    assert rows["main"][0] == "protected" and rows["staging"][0] == "protected", rows


def test_tags_missing_and_conflicting():
    work = setup()
    git(work, "tag", "v1")
    git(work, "push", "-q", "origin", "v1")
    git(work, "commit", "-q", "--allow-empty", "-m", "x")
    git(work, "tag", "v2")
    git(work, "push", "-q", "origin", "v2")
    git(work, "tag", "-f", "v2", "HEAD~1")
    git(work, "push", "-q", "lab", "v2")
    _, rows = plan(work)
    assert rows["v1"][0] == "tag-push" and rows["v2"][0] == "tag-conflict", rows


def test_needs_two_remotes():
    work = setup()
    git(work, "remote", "remove", "lab")
    code, rows = plan(work)
    assert code == 3 and rows["origin"][0] == "remote", rows


def test_named_remotes_override_detection():
    work = setup()
    git(work, "remote", "rename", "lab", "mirror")
    code, rows = plan(work, "origin", "mirror")
    assert code == 0 and rows["main"][0] == "same", rows


def test_summary_counts_every_kind():
    work = setup()
    commit_and_push(work, "feat/a", "origin")
    git(work, "tag", "v1")
    git(work, "push", "-q", "origin", "v1")
    _, rows = plan(work)
    kind, _, counts, _ = rows["counts"]
    assert kind == "summary" and counts == "same=1 push=1 protected=0 diverged=0 tag-push=1 tag-conflict=0", counts


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_sync_remote: {len(tests)} passed")
