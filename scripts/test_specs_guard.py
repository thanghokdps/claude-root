#!/usr/bin/env python3
"""Tests for plugins/core/hooks/specs-guard.sh. Run: python3 scripts/test_specs_guard.py"""
import json
import os
import subprocess
import tempfile

from harness_state import specs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "core", "hooks", "specs-guard.sh")


def repo():
    path = os.path.realpath(tempfile.mkdtemp(prefix="specs-guard-"))
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    return path


def decision(path, file_path, tool="Write"):
    ev = {"cwd": path, "tool_name": tool, "tool_input": {"file_path": file_path}}
    r = subprocess.run([HOOK], input=json.dumps(ev), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)["hookSpecificOutput"] if r.stdout else None


def test_write_into_repo_specs_is_denied_and_names_the_state_dir():
    path = repo()
    out = decision(path, os.path.join(path, "specs", "feat", "PLAN.md"))
    assert out["permissionDecision"] == "deny"
    assert specs(path, "feat", "PLAN.md") in out["permissionDecisionReason"]


def test_other_paths_and_the_state_dir_pass():
    path = repo()
    for f in (os.path.join(path, "src", "specs.ts"), os.path.join(path, "docs", "specs", "a.md"),
              specs(path, "feat", "PLAN.md")):
        assert decision(path, f) is None, f


def test_a_repo_that_tracks_specs_keeps_them():
    path = repo()
    os.makedirs(os.path.join(path, "specs"))
    open(os.path.join(path, "specs", "api.md"), "w").write("x\n")
    subprocess.run(["git", "-C", path, "add", "specs"], check=True)
    assert decision(path, os.path.join(path, "specs", "new.md"), "Edit") is None


def test_garbage_and_no_repo_pass():
    r = subprocess.run([HOOK], input="nope", capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout == ""
    assert decision(tempfile.mkdtemp(), "/tmp/x/specs/a.md") is None


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_specs_guard: {len(tests)} passed")
