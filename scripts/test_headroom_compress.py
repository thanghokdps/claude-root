#!/usr/bin/env python3
"""Tests for plugins/guards/hooks/headroom-compress.sh. Run: python3 scripts/test_headroom_compress.py"""
import json
import os
import subprocess
import tempfile
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "guards", "hooks", "headroom-compress.sh")


def home(registered):
    path = tempfile.mkdtemp(prefix="headroom-home-")
    with open(os.path.join(path, ".claude.json"), "w") as f:
        json.dump({"mcpServers": {"headroom": {}} if registered else {}}, f)
    return path


def run(home_dir, tmp_dir, size, sid=None, cwd=None, threshold=None):
    event = {"hook_event_name": "PostToolUse", "tool_name": "Bash", "cwd": cwd or home_dir,
             "session_id": sid or uuid.uuid4().hex, "tool_input": {"command": "cat big.log"},
             "tool_response": {"stdout": "x" * size}}
    env = {**os.environ, "HOME": home_dir, "TMPDIR": tmp_dir}
    if threshold:
        env["HEADROOM_WARN_THRESHOLD"] = threshold
    return subprocess.run([HOOK], input=json.dumps(event), capture_output=True, text=True, env=env, cwd=cwd)


def test_empty_input_is_a_noop():
    env = {**os.environ, "HOME": home(True)}
    for data in ["{}", ""]:
        r = subprocess.run([HOOK], input=data, capture_output=True, text=True, env=env)
        assert r.returncode == 0 and r.stdout == ""


def test_small_output_and_unregistered_mcp_stay_silent():
    tmp = tempfile.mkdtemp()
    r = run(home(True), tmp, 100)
    assert r.returncode == 0 and r.stdout == ""
    r = run(home(False), tmp, 50000)
    assert r.returncode == 0 and r.stdout == ""


def test_huge_output_with_headroom_registered_hints_once_per_session():
    h, tmp = home(True), tempfile.mkdtemp()
    r = run(h, tmp, 50000, sid="s1")
    assert r.returncode == 0
    out = json.loads(r.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PostToolUse" and out["additionalContext"].startswith("headroom: that Bash output")
    assert os.path.exists(os.path.join(tmp, "headroom-hinted-s1"))
    again = run(h, tmp, 50000, sid="s1")
    assert again.returncode == 0 and again.stdout == ""
    assert run(h, tmp, 50000, sid="s2").stdout != ""


def test_threshold_env_and_cwd_independence():
    h, tmp = home(True), tempfile.mkdtemp()
    elsewhere = tempfile.mkdtemp()
    r = run(h, tmp, 1000, cwd=elsewhere)
    assert r.returncode == 0 and r.stdout == ""
    r = run(h, tmp, 1000, cwd=elsewhere, threshold="500")
    assert r.returncode == 0 and "headroom:" in r.stdout


def test_event_cwd_is_accepted_from_an_unrelated_process_cwd():
    h, tmp = home(True), tempfile.mkdtemp()
    fixture, elsewhere = tempfile.mkdtemp(prefix="headroom-fixture-"), tempfile.mkdtemp(prefix="headroom-else-")
    event = {"hook_event_name": "PostToolUse", "tool_name": "Bash", "cwd": fixture, "session_id": "cwd1",
             "tool_input": {"command": "cat big.log"}, "tool_response": {"stdout": "x" * 50000}}
    env = {**os.environ, "HOME": h, "TMPDIR": tmp}
    r = subprocess.run([HOOK], input=json.dumps(event), capture_output=True, text=True, env=env, cwd=elsewhere)
    assert r.returncode == 0 and "headroom:" in r.stdout


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
