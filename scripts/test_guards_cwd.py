#!/usr/bin/env python3
"""Guards hooks act on the event's cwd, not CLAUDE_PROJECT_DIR. Run: python3 scripts/test_guards_cwd.py

In a worktree session CLAUDE_PROJECT_DIR is the main checkout while the command runs in the worktree;
each case gives the two different contents and checks the hook used the worktree's."""
import datetime
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "plugins", "guards", "hooks")


def repo(branch):
    path = tempfile.mkdtemp(prefix="guards-cwd-")
    git = lambda *a: subprocess.run(["git", "-C", path, *a], check=True, capture_output=True)
    git("init", "-q", "-b", branch)
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", f"init {branch}")
    return path


def project_with_worktree():
    root = repo("main")
    wt = os.path.join(tempfile.mkdtemp(prefix="guards-wt-"), "wt")
    subprocess.run(["git", "-C", root, "worktree", "add", "-q", "-b", "feat/x", wt], check=True, capture_output=True)
    return root, wt


def write(path, name, text=""):
    os.makedirs(os.path.dirname(os.path.join(path, name)), exist_ok=True)
    with open(os.path.join(path, name), "w") as f:
        f.write(text)


def run(hook, root, cwd, payload=None, path=None):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": root}
    if path:
        env["PATH"] = path + os.pathsep + env["PATH"]
    event = {"cwd": cwd, **(payload or {})}
    # The hook process itself starts in the project root, as Claude Code starts it.
    return subprocess.run([os.path.join(HOOKS, hook)], input=json.dumps(event), capture_output=True,
                          text=True, env=env, cwd=root)


def test_commit_quality_gate_reads_the_worktree_index():
    root, wt = project_with_worktree()
    write(wt, ".env", "KEY=1\n")
    subprocess.run(["git", "-C", wt, "add", "-f", ".env"], check=True)
    out = run("commit-quality-gate.sh", root, wt, {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}})
    assert out.returncode == 2 and ".env" in out.stderr, out.stderr


def test_commit_quality_gate_scans_a_repo_outside_the_project_without_running_its_config():
    root, other = repo("main"), repo("feat/x")
    pwned = os.path.join(other, "PWNED")
    subprocess.run(["git", "-C", other, "config", "diff.t.textconv", f"touch {pwned}; cat"], check=True)
    subprocess.run(["git", "-C", other, "config", "diff.external", f"touch {pwned}"], check=True)
    write(other, ".gitattributes", "*.js diff=t\n")
    write(other, "a.js", "console.log(1)\n")
    write(other, ".env", "KEY=1\n")
    subprocess.run(["git", "-C", other, "add", "-f", ".gitattributes", "a.js", ".env"], check=True)
    out = run("commit-quality-gate.sh", root, other, {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}})
    assert out.returncode == 2 and ".env" in out.stderr, out.stderr
    assert not os.path.exists(pwned)


def test_format_on_edit_runs_in_the_worktree():
    root, wt = project_with_worktree()
    write(wt, ".prettierrc", "{}\n")
    write(wt, "a.ts", "x\n")
    bin_dir, log = tempfile.mkdtemp(), os.path.join(tempfile.mkdtemp(), "npx.log")
    write(bin_dir, "npx", f'#!/bin/sh\npwd > "{log}"\n')
    os.chmod(os.path.join(bin_dir, "npx"), 0o755)
    run("format-on-edit.sh", root, wt, {"tool_input": {"file_path": os.path.join(wt, "a.ts")}}, path=bin_dir)
    assert os.path.realpath(open(log).read().strip()) == os.path.realpath(wt)


def test_session_resume_injects_the_worktree_handoff():
    root, wt = project_with_worktree()
    write(root, "specs/HANDOFF.md", "ROOT-HANDOFF\n")
    write(wt, "specs/HANDOFF.md", "WORKTREE-HANDOFF\n")
    ctx = json.loads(run("session-resume.sh", root, wt).stdout)["hookSpecificOutput"]["additionalContext"]
    assert "WORKTREE-HANDOFF" in ctx and "ROOT-HANDOFF" not in ctx


def test_session_handoff_describes_the_worktree():
    root, wt = project_with_worktree()
    run("session-handoff.sh", root, wt)
    assert not os.path.exists(os.path.join(root, "specs", "HANDOFF.md"))
    assert "feat/x" in open(os.path.join(wt, "specs", "HANDOFF.md")).read()


def test_state_breadcrumb_writes_into_the_worktree():
    root, wt = project_with_worktree()
    for r in (root, wt):
        os.makedirs(os.path.join(r, ".claude", "memory"))
    run("state-breadcrumb.sh", root, wt, {"session_id": "s1"})
    today = datetime.date.today().isoformat()
    assert not os.path.exists(os.path.join(root, ".claude", "memory", "sessions", f"{today}.md"))
    assert "feat/x" in open(os.path.join(wt, ".claude", "memory", "sessions", f"{today}.md")).read()


def test_save_commit_memory_logs_the_worktree_commit():
    root, wt = project_with_worktree()
    subprocess.run(["git", "-C", wt, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty",
                    "-m", "worktree commit"], check=True)
    for r in (root, wt):
        os.makedirs(os.path.join(r, ".claude", "memory"), exist_ok=True)
    run("save-commit-memory.sh", root, wt, {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}})
    log = os.path.join(wt, ".claude", "memory", "commits", f"{datetime.date.today().isoformat()}.md")
    assert "worktree commit" in open(log).read()
    assert not os.path.exists(os.path.join(root, ".claude", "memory", "commits"))


def test_a_folder_outside_the_project_is_not_trusted():
    root, other = repo("main"), repo("feat/x")  # e.g. a repo the shell cloned and cd'd into
    write(root, "specs/HANDOFF.md", "ROOT-HANDOFF\n")
    write(other, "specs/HANDOFF.md", "OTHER-HANDOFF\n")
    ctx = json.loads(run("session-resume.sh", root, other).stdout)["hookSpecificOutput"]["additionalContext"]
    assert "ROOT-HANDOFF" in ctx and "OTHER-HANDOFF" not in ctx
    write(other, ".prettierrc", "{}\n")
    write(other, "a.ts", "x\n")
    bin_dir, log = tempfile.mkdtemp(), os.path.join(tempfile.mkdtemp(), "npx.log")
    write(bin_dir, "npx", f'#!/bin/sh\npwd > "{log}"\n')
    os.chmod(os.path.join(bin_dir, "npx"), 0o755)
    run("format-on-edit.sh", root, other, {"tool_input": {"file_path": os.path.join(other, "a.ts")}}, path=bin_dir)
    assert not os.path.exists(log)  # the project has no prettier config, so nothing ran


def test_without_a_cwd_the_project_dir_still_works():
    root = repo("feat/y")
    write(root, "specs/HANDOFF.md", "ROOT-HANDOFF\n")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": root}
    out = subprocess.run([os.path.join(HOOKS, "session-resume.sh")], input="{}", capture_output=True, text=True, env=env)
    assert "ROOT-HANDOFF" in out.stdout


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_guards_cwd: {len(tests)} passed")
