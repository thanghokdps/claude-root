#!/usr/bin/env python3
"""Tests for plugins/core/hooks/missing-tools.sh. Run: python3 scripts/test_missing_tools.py"""
import json
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "core", "hooks", "missing-tools.sh")
BASH = shutil.which("bash")


def run(*tools):
    """Run the hook with a PATH holding only the named tools."""
    path = tempfile.mkdtemp(prefix="missing-tools-")
    for tool in tools:
        target = os.path.join(path, tool)
        with open(target, "w") as f:
            f.write("#!/bin/sh\n")
        os.chmod(target, 0o755)
    r = subprocess.run([BASH, HOOK], input="{}", capture_output=True, text=True, env={"PATH": path})
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_quiet_when_both_tools_are_there():
    assert run("python3", "jq") == ""


def test_both_missing_is_valid_json_for_the_user_and_the_model():
    out = json.loads(run())
    assert "not installed: python3 jq." in out["systemMessage"], out
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "first reply" in out["hookSpecificOutput"]["additionalContext"], out


def test_names_only_the_tool_that_is_missing():
    assert "not installed: jq." in json.loads(run("python3"))["systemMessage"]
    assert "not installed: python3." in json.loads(run("jq"))["systemMessage"]


def test_registered_at_session_start():
    with open(os.path.join(ROOT, "plugins", "core", "hooks", "hooks.json")) as f:
        hooks = json.load(f)["hooks"]["SessionStart"]
    commands = [h["command"] for group in hooks for h in group["hooks"]]
    assert any(c.endswith("/hooks/missing-tools.sh") for c in commands), commands


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"missing-tools tests: {len(tests)} passed")
