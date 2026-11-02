#!/usr/bin/env python3
"""Tests for plugins/guards/hooks/risk-corroboration.sh. Run: python3 scripts/test_risk_corroboration.py

The hook finds the repo from the event's cwd (falling back to its process cwd), then git rev-parse."""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "guards", "hooks", "risk-corroboration.sh")


def write(path, name, text=""):
    full = os.path.join(path, name)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(text)


def repo(lane=None, risky=True):
    path = tempfile.mkdtemp(prefix="risk-")
    git = lambda *a: subprocess.run(["git", "-C", path, *a], check=True, capture_output=True)
    git("init", "-q")
    if lane:
        write(path, "specs/x/SUMMARY.md", f"Lane: {lane}\n")
    if risky:
        write(path, "db/migrations/001_init.sql", "CREATE TABLE t (id int);\n")
        write(path, "src/auth.py", "def login(password):\n    return bcrypt.hashpw(password)\n")
        git("add", "src", "db")
    else:
        write(path, "src/ok.py", "x = 1\n")
        git("add", "src")
    return path


def run(cwd, command="git commit -m x", payload_cwd=None):
    event = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "cwd": payload_cwd or cwd,
             "tool_input": {"command": command}}
    return subprocess.run([HOOK], input=json.dumps(event), capture_output=True, text=True, cwd=cwd)


def test_empty_input_is_a_noop():
    r = subprocess.run([HOOK], input="{}", capture_output=True, text=True, cwd=repo("normal"))
    assert r.returncode == 0 and r.stdout == "" and r.stderr == ""


def test_non_commit_commands_and_clean_diffs_pass():
    assert run(repo("tiny"), "git status").returncode == 0
    assert run(repo("tiny", risky=False)).returncode == 0
    empty = tempfile.mkdtemp(prefix="risk-empty-")
    subprocess.run(["git", "-C", empty, "init", "-q"], check=True)
    assert run(empty).returncode == 0


def test_risky_diff_with_low_lane_is_blocked():
    for lane in ["tiny", "normal"]:
        out = run(repo(lane))
        assert out.returncode == 2, lane
        assert "[RISK CORROBORATION] BLOCKED." in out.stderr
        assert f"SUMMARY.md declares Lane: {lane}" in out.stderr
        assert "auth" in out.stderr and "data-loss/migration" in out.stderr


def test_risky_diff_with_high_risk_lane_is_allowed():
    out = run(repo("high-risk"))
    assert out.returncode == 0 and "corroborated by Lane: high-risk" in out.stderr


def test_risky_diff_without_lane_warns_but_allows():
    out = run(repo(None))
    assert out.returncode == 0 and "no declared Lane" in out.stderr


def test_follows_the_event_cwd_not_the_process_cwd():
    blocked, clean = repo("normal"), repo("normal", risky=False)
    assert run(clean, payload_cwd=blocked).returncode == 2
    assert run(blocked, payload_cwd=clean).returncode == 0
    elsewhere = tempfile.mkdtemp(prefix="risk-else-")
    assert run(elsewhere, payload_cwd=blocked).returncode == 2


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
