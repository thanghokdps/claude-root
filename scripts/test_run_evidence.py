#!/usr/bin/env python3
"""Tests for core step-limit.sh, guards run-log.sh, push-evidence.sh, create-pr's witness.sh and blast-radius's hotspots.sh. Run: python3 scripts/test_run_evidence.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP = os.path.join(ROOT, "plugins", "core", "hooks", "step-limit.sh")
RUNLOG = os.path.join(ROOT, "plugins", "guards", "hooks", "run-log.sh")
WITNESS = os.path.join(ROOT, "plugins", "review", "skills", "create-pr", "scripts", "witness.sh")
PUSH = os.path.join(ROOT, "plugins", "guards", "hooks", "push-evidence.sh")
HOTSPOTS = os.path.join(ROOT, "plugins", "review", "skills", "blast-radius", "scripts", "hotspots.sh")


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


def pushed_repo(check_ts=None):
    """A clone with one unpushed commit; check_ts, if set, is the time of a logged test run."""
    origin = repo()
    run = lambda *a, cwd: subprocess.run(["git", "-C", cwd, *a], check=True, capture_output=True)
    run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "base", cwd=origin)
    path = tempfile.mkdtemp(prefix="push-evidence-")
    subprocess.run(["git", "clone", "-q", origin, path], check=True, capture_output=True)
    with open(os.path.join(path, "app.py"), "w") as f:
        f.write("x = 1\n")
    os.utime(os.path.join(path, "app.py"), (1_800_000_000, 1_800_000_000))  # 2027-01-15
    run("add", "app.py", cwd=path)
    run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "change", cwd=path)
    if check_ts:
        with open(os.path.join(path, ".git", "claude-run-log.jsonl"), "w") as f:
            f.write(json.dumps({"ts": check_ts, "cmd": "npm test", "last": "ok", "interrupted": False}) + "\n")
    return path


def push(path, command="git push"):
    payload = json.dumps({"tool_input": {"command": command}, "cwd": path})
    r = subprocess.run([PUSH], input=payload, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_push_without_a_later_check_asks():
    out = push(pushed_repo("2026-01-01T00:00:00Z"))
    assert '"permissionDecision":"ask"' in out and "before the last change" in out, out


def test_push_after_a_check_is_silent():
    assert push(pushed_repo("2028-01-01T00:00:00Z")) == ""


def test_push_gate_ignores_other_commands_and_missing_log():
    path = pushed_repo("2026-01-01T00:00:00Z")
    assert push(path, "git status") == ""
    assert push(pushed_repo(), "gh pr create --fill") == ""


def test_hotspots_rank_changed_files_and_skip_lockfiles():
    path = repo()
    for i in range(3):
        for name in (["app.py", "package-lock.json"] if i else ["app.py", "package-lock.json", "util.py"]):
            with open(os.path.join(path, name), "a") as f:
                f.write(f"{i}\n")
        subprocess.run(["git", "-C", path, "add", "-A"], check=True)
        subprocess.run(["git", "-C", path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", str(i)], check=True)
    out = subprocess.run(["bash", HOTSPOTS], capture_output=True, text=True, cwd=path).stdout.split("\n")
    assert out[0].split() == ["3", "app.py"] and out[1].split() == ["1", "util.py"], out
    assert not any("package-lock.json" in line for line in out), out


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_run_evidence: {len(tests)} passed")
