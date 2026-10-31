#!/usr/bin/env python3
"""Tests for plugins/guards/hooks/agent-progress.sh. Run: python3 scripts/test_agent_progress.py

The hook writes to $HOME/.claude/progress.log and reads specs/**/WAVE_STATE.json under its own process cwd."""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "guards", "hooks", "agent-progress.sh")


def sandbox():
    home = tempfile.mkdtemp(prefix="progress-home-")
    os.makedirs(os.path.join(home, ".claude"))
    return home, tempfile.mkdtemp(prefix="progress-cwd-")


def log(home):
    try:
        with open(os.path.join(home, ".claude", "progress.log")) as f:
            return f.read()
    except FileNotFoundError:
        return ""


def run(home, cwd, tool, tool_input, *args):
    event = {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": cwd, "tool_input": tool_input}
    return subprocess.run([HOOK, *args], input=json.dumps(event), capture_output=True, text=True,
                          env={**os.environ, "HOME": home}, cwd=cwd)


def test_empty_input_exits_zero_and_logs_nothing():
    home, cwd = sandbox()
    r = subprocess.run([HOOK], input="{}", capture_output=True, text=True, env={**os.environ, "HOME": home}, cwd=cwd)
    assert r.returncode == 0 and r.stdout == "" and log(home) == ""


def test_agent_pre_logs_spawn_and_prints_hint():
    home, cwd = sandbox()
    r = run(home, cwd, "Agent", {"description": "build api", "subagent_type": "dev:backend", "run_in_background": True}, "pre")
    assert r.returncode == 0
    assert r.stdout.strip() == "[agent-progress] Spawning dev:backend — build api (⚡ PARALLEL (background))"
    text = log(home)
    assert "AGENT SPAWN" in text and "build api" in text and "dev:backend" in text


def test_agent_pre_blocking_mode_and_post_done():
    home, cwd = sandbox()
    r = run(home, cwd, "Agent", {"description": "write docs"}, "pre")
    assert r.returncode == 0 and "SEQUENTIAL (blocking)" in r.stdout and "general-purpose" in r.stdout
    r = run(home, cwd, "Agent", {"description": "write docs"})
    assert r.returncode == 0 and r.stdout.strip() == "[agent-progress] Agent done — write docs"
    assert "AGENT DONE  write docs" in log(home)


def test_edit_and_write_log_path_relative_to_process_cwd():
    home, cwd = sandbox()
    assert run(home, cwd, "Edit", {"file_path": os.path.join(os.getcwd(), "x")}).returncode == 0
    # The hook strips "$(pwd)/", which is the physical cwd (macOS resolves /var -> /private/var).
    real = os.path.realpath(cwd)
    assert run(home, cwd, "Edit", {"file_path": os.path.join(real, "src/a.ts")}).returncode == 0
    assert run(home, cwd, "Write", {"file_path": os.path.join(real, "src/b.ts")}).returncode == 0
    text = log(home)
    assert "EDIT   src/a.ts" in text and "WRITE  src/b.ts" in text


def test_bash_logs_only_dev_commands():
    home, cwd = sandbox()
    assert run(home, cwd, "Bash", {"command": "ls -la"}).returncode == 0
    assert log(home) == ""
    assert run(home, cwd, "Bash", {"command": "pytest -q tests/"}).returncode == 0
    assert "BASH   pytest -q tests/" in log(home)


def test_wave_board_follows_the_cwd_the_hook_runs_in():
    home, cwd = sandbox()
    other = tempfile.mkdtemp(prefix="progress-other-")
    state = {"slug": "demo", "issue": "#7", "waves": [{"wave": 1, "tasks": [
        {"title": "first task", "status": "in_progress", "agent": "backend"},
        {"title": "second task", "status": "pending", "blocked_by": [1]}]}]}
    os.makedirs(os.path.join(cwd, "specs", "demo"))
    with open(os.path.join(cwd, "specs", "demo", "WAVE_STATE.json"), "w") as f:
        json.dump(state, f)
    r = run(home, cwd, "Agent", {"description": "d"}, "pre")
    assert r.returncode == 0
    text = log(home)
    assert "WAVE BOARD" in text and "first task" in text and "second task" in text and "NOW" in text
    home2, _ = sandbox()
    run(home2, other, "Agent", {"description": "d"}, "pre")
    assert "WAVE BOARD" not in log(home2)


def test_event_cwd_beats_an_unrelated_process_cwd():
    home, fixture = sandbox()
    elsewhere = tempfile.mkdtemp(prefix="progress-else-")
    os.makedirs(os.path.join(fixture, "specs", "demo"))
    with open(os.path.join(fixture, "specs", "demo", "WAVE_STATE.json"), "w") as f:
        json.dump({"slug": "demo", "waves": [{"wave": 1, "tasks": [{"title": "fixture task", "status": "pending"}]}]}, f)
    event = {"hook_event_name": "PreToolUse", "tool_name": "Agent", "cwd": fixture, "tool_input": {"description": "d"}}
    r = subprocess.run([HOOK, "pre"], input=json.dumps(event), capture_output=True, text=True,
                       env={**os.environ, "HOME": home}, cwd=elsewhere)
    assert r.returncode == 0 and "fixture task" in log(home)
    edit = {"tool_name": "Edit", "cwd": fixture, "tool_input": {"file_path": os.path.join(os.path.realpath(fixture), "src/c.ts")}}
    subprocess.run([HOOK], input=json.dumps(edit), capture_output=True, text=True, env={**os.environ, "HOME": home}, cwd=elsewhere)
    assert "EDIT   src/c.ts" in log(home)


def test_unhandled_tool_never_blocks():
    home, cwd = sandbox()
    r = run(home, cwd, "Read", {"file_path": "/x"})
    assert r.returncode == 0 and r.stdout == "" and log(home) == ""


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
