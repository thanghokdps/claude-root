#!/usr/bin/env python3
"""Tests for guards step-limit.sh, run-log.sh and create-pr's witness.sh. Run: python3 scripts/test_run_evidence.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP = os.path.join(ROOT, "plugins", "guards", "hooks", "step-limit.sh")
RUNLOG = os.path.join(ROOT, "plugins", "guards", "hooks", "run-log.sh")
WITNESS = os.path.join(ROOT, "plugins", "review", "skills", "create-pr", "scripts", "witness.sh")


def step(payload, tmp, **env):
    e = {**os.environ, "TMPDIR": tmp, **env}
    return subprocess.run([STEP], input=json.dumps(payload), capture_output=True, text=True, env=e)


def repo():
    path = tempfile.mkdtemp(prefix="run-evidence-")
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    return path


def test_subagent_is_stopped_past_the_limit():
    tmp = tempfile.mkdtemp()
    p = {"session_id": "s", "agent_id": "a", "tool_name": "Bash"}
    assert [step(p, tmp, CLAUDE_STEP_LIMIT="2").returncode for _ in range(3)] == [0, 0, 2]
    assert "Step limit reached" in step(p, tmp, CLAUDE_STEP_LIMIT="2").stderr


def test_counters_are_per_agent_and_main_is_free():
    tmp = tempfile.mkdtemp()
    for _ in range(3):
        step({"session_id": "s", "agent_id": "a"}, tmp, CLAUDE_STEP_LIMIT="2")
    assert step({"session_id": "s", "agent_id": "b"}, tmp, CLAUDE_STEP_LIMIT="2").returncode == 0
    assert step({"session_id": "s"}, tmp, CLAUDE_STEP_LIMIT="0").returncode == 0
    assert step({"session_id": "s"}, tmp, CLAUDE_STEP_LIMIT="0", CLAUDE_STEP_LIMIT_MAIN="1").returncode == 2


def test_empty_input_never_blocks():
    assert step({}, tempfile.mkdtemp()).returncode == 0


def test_run_log_feeds_witness():
    path = repo()
    payload = {"session_id": "s", "tool_input": {"command": "npm test"},
               "tool_response": {"stdout": "x\nTests: 12 passed\n", "interrupted": False}}
    for cmd in ["npm test", "ls -la"]:
        payload["tool_input"]["command"] = cmd
        r = subprocess.run([RUNLOG], input=json.dumps(payload), capture_output=True, text=True, cwd=path)
        assert r.returncode == 0
    out = subprocess.run(["bash", WITNESS], capture_output=True, text=True, cwd=path).stdout
    assert "`npm test`" in out and "Tests: 12 passed" in out, out
    assert "ls -la" not in out, out


def test_witness_without_log_says_not_recorded():
    out = subprocess.run(["bash", WITNESS], capture_output=True, text=True, cwd=repo()).stdout
    assert "not recorded" in out, out


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_run_evidence: {len(tests)} passed")
