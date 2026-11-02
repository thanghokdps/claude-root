#!/usr/bin/env python3
"""Tests for plugins/guards/hooks/notify-on-finish.sh. Run: python3 scripts/test_notify_on_finish.py"""
import json
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "guards", "hooks", "notify-on-finish.sh")
BASH = shutil.which("bash")


def bin_dir(with_osascript):
    d = tempfile.mkdtemp(prefix="notify-bin-")
    marker = os.path.join(d, "called")
    os.symlink(shutil.which("basename"), os.path.join(d, "basename"))
    if with_osascript:
        stub = os.path.join(d, "osascript")
        with open(stub, "w") as f:
            f.write(f'#!/bin/sh\nprintf "%s\\n" "$*" > "{marker}"\n')
        os.chmod(stub, 0o755)
    return d, marker


def run(path_dir, payload, project=None, cwd=None):
    env = {"PATH": path_dir, "HOME": tempfile.mkdtemp()}
    if project:
        env["CLAUDE_PROJECT_DIR"] = project
    return subprocess.run([BASH, HOOK], input=json.dumps(payload), capture_output=True, text=True, env=env, cwd=cwd)


def test_empty_input_exits_zero():
    d, marker = bin_dir(False)
    r = run(d, {})
    assert r.returncode == 0 and r.stdout == "" and not os.path.exists(marker)


def test_no_osascript_runs_nothing():
    d, marker = bin_dir(False)
    r = run(d, {"hook_event_name": "Stop", "cwd": d})
    assert r.returncode == 0 and r.stdout == "" and r.stderr == "" and not os.path.exists(marker)


def test_osascript_present_is_called_with_project_name():
    d, marker = bin_dir(True)
    r = run(d, {"hook_event_name": "Stop"}, project="/work/my-app")
    assert r.returncode == 0
    with open(marker) as f:
        args = f.read()
    assert "display notification" in args and "Claude · my-app" in args


def test_project_name_follows_process_cwd_when_no_env():
    d, marker = bin_dir(True)
    other = tempfile.mkdtemp(prefix="elsewhere-")
    r = run(d, {"hook_event_name": "Stop"}, cwd=other)
    assert r.returncode == 0
    with open(marker) as f:
        assert os.path.basename(other) in f.read()


def test_project_name_follows_event_cwd_not_process_cwd():
    d, marker = bin_dir(True)
    os.symlink(shutil.which("jq"), os.path.join(d, "jq"))
    fixture = os.path.join(tempfile.mkdtemp(prefix="notify-"), "fixture-app")
    os.makedirs(fixture)
    other = tempfile.mkdtemp(prefix="elsewhere-")
    r = run(d, {"hook_event_name": "Stop", "cwd": fixture}, cwd=other)
    assert r.returncode == 0
    with open(marker) as f:
        text = f.read()
    assert "Claude · fixture-app" in text and os.path.basename(other) not in text


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
