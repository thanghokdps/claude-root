#!/usr/bin/env python3
"""Tests for scripts/remote-drift.sh (install.sh's remote check). Run: python3 scripts/test_remote_drift.py"""
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "remote-drift.sh")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]


def git(path, *args):
    return subprocess.run(GIT + ["-C", path, *args], check=True, capture_output=True, text=True).stdout.strip()


def kit():
    """A kit checkout with two bare remotes, as here: origin (personal) and gitlab (company copy)."""
    base = tempfile.mkdtemp(prefix="drift-")
    remotes = {}
    for name in ("origin", "gitlab"):
        remotes[name] = os.path.join(base, f"{name}.git")
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", remotes[name]], check=True)
    path = os.path.join(base, "kit")
    subprocess.run(["git", "init", "-q", "-b", "main", path], check=True)
    for name, url in remotes.items():
        git(path, "remote", "add", name, url)
    git(path, "commit", "-q", "--allow-empty", "-m", "init")
    git(path, "push", "-q", "origin", "main")
    git(path, "push", "-q", "gitlab", "main")
    return path, remotes


def run(path, source):
    out = subprocess.run(["bash", SCRIPT, path, source], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout


def test_source_carrying_the_other_remote_plus_its_own_merge_is_quiet():
    path, remotes = kit()
    git(path, "commit", "-q", "--allow-empty", "-m", "feature on main")
    git(path, "push", "-q", "origin", "main")
    git(path, "switch", "-q", "-c", "company", "HEAD~1")
    git(path, "merge", "-q", "--no-ff", "main", "-m", "Merge main into company")
    git(path, "push", "-q", "gitlab", "company:main")
    git(path, "switch", "-q", "main")
    assert run(path, f"Git ({remotes['gitlab']})") == ""


def test_source_behind_the_other_remote_warns():
    path, remotes = kit()
    git(path, "commit", "-q", "--allow-empty", "-m", "feature on main")
    git(path, "push", "-q", "origin", "main")
    out = run(path, f"Git ({remotes['gitlab']})")
    assert "gitlab (the install source) lacks commits from: origin" in out
    assert "origin " in out and "gitlab " in out


def test_equal_remotes_are_quiet():
    path, remotes = kit()
    assert run(path, f"Git ({remotes['gitlab']})") == ""
    assert run(path, f"Folder ({path})") == ""


def test_folder_install_with_diverged_remotes_warns():
    path, _ = kit()
    git(path, "commit", "-q", "--allow-empty", "-m", "feature on main")
    git(path, "push", "-q", "origin", "main")
    assert "the kit's remotes point at different commits" in run(path, f"Folder ({path})")


def test_kit_without_two_remotes_is_quiet():
    path = tempfile.mkdtemp(prefix="drift-solo-")
    subprocess.run(["git", "init", "-q", path], check=True)
    assert run(path, f"Folder ({path})") == ""


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("remote drift: all tests passed")
