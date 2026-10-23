#!/usr/bin/env python3
"""Tests for plugins/guards/hooks/branch-guard.sh. Run: python3 scripts/test_branch_guard.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "guards", "hooks", "branch-guard.sh")


def repo_on(branch):
    path = tempfile.mkdtemp(prefix="branch-guard-")
    git = lambda *a: subprocess.run(["git", "-C", path, *a], check=True, capture_output=True)
    git("init", "-q", "-b", branch)
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init")
    return path


def exit_code(command, branch="feat/x"):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": repo_on(branch)}
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    return subprocess.run([HOOK], input=payload, capture_output=True, text=True, env=env).returncode


def test_force_push_to_a_protected_branch_is_blocked():
    for cmd in ["git push -f origin main", "git push --force origin master", "git push --force-with-lease origin dev",
                "git push origin +main", "git push -uf origin main", "git push origin HEAD:main --force"]:
        assert exit_code(cmd) == 2, cmd
    assert exit_code("git push --force", branch="main") == 2


def test_dash_f_inside_a_branch_name_is_not_a_force_flag():
    assert exit_code("git push -u origin feat/dev-fullstack-skills", branch="feat/dev-fullstack-skills") == 0
    assert exit_code("git push -u origin feat/agent-tool-from-api 2>&1 | tail -1") == 0


def test_flags_and_branch_names_after_the_push_belong_to_other_commands():
    assert exit_code("git push -u origin feat/x && gh pr create --base main --body-file body.md") == 0


def test_branch_merely_containing_a_protected_name_is_not_protected():
    assert exit_code("git push --force origin feat/dev-tools", branch="feat/dev-tools") == 0
    assert exit_code("git push --force origin fix/main-menu") == 0


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_branch_guard: {len(tests)} passed")
