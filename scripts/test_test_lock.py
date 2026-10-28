#!/usr/bin/env python3
"""Tests for plugins/dev/hooks/test-lock.sh and fix-bug/scripts/lock-tests.sh. Run: python3 scripts/test_test_lock.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "dev", "hooks", "test-lock.sh")
LOCKER = os.path.join(ROOT, "plugins", "dev", "skills", "fix-bug", "scripts", "lock-tests.sh")


def repo():
    path = tempfile.mkdtemp(prefix="test-lock-")
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    os.makedirs(os.path.join(path, "src"))
    for name in ("src/bug.test.ts", "src/app.ts"):
        with open(os.path.join(path, name), "w") as f:
            f.write("original\n")
    return path


def locker(cwd, *args):
    return subprocess.run(["bash", LOCKER, *args], cwd=cwd, capture_output=True, text=True)


def hook(cwd, tool, **tool_input):
    payload = json.dumps({"tool_name": tool, "cwd": cwd, "tool_input": tool_input})
    return subprocess.run([HOOK], input=payload, capture_output=True, text=True).returncode


def locked_repo():
    path = repo()
    assert locker(path, "lock", "src/bug.test.ts").returncode == 0
    return path


def test_edits_of_a_locked_file_are_blocked():
    r = locked_repo()
    full = os.path.join(r, "src/bug.test.ts")
    assert hook(r, "Edit", file_path=full) == 2
    assert hook(r, "Write", file_path=full) == 2
    assert hook(r, "MultiEdit", file_path="src/bug.test.ts") == 2
    assert hook(r, "NotebookEdit", notebook_path=full) == 2


def test_other_files_and_unlocked_edits_pass():
    r = locked_repo()
    assert hook(r, "Edit", file_path=os.path.join(r, "src/app.ts")) == 0
    assert locker(r, "unlock").returncode == 0
    assert hook(r, "Edit", file_path=os.path.join(r, "src/bug.test.ts")) == 0


def test_bash_that_undoes_the_lock_is_blocked():
    r = locked_repo()
    for cmd in ["git checkout -- src/bug.test.ts", "git restore src/bug.test.ts", "rm src/bug.test.ts",
                "mv src/bug.test.ts /tmp/x", "git stash", "rm .git/claude-fix-lock.json",
                "echo '{}' > .git/claude-fix-lock.json", f"bash {LOCKER} check; rm .git/claude-fix-lock.json",
                "git reset --hard", "git reset --keep HEAD~1", "git checkout -- src/", "git restore src",
                "rm -rf ./src", "git checkout -- ':/src'", "git restore 'src/*.ts'", f"git checkout -- {os.path.join(r, 'src')}", "git checkout -- 'src/bu*'", "git checkout -- '*'",
                "git -C src checkout -- .", "git -C src checkout -- bug.test.ts",
                "git checkout .", "git restore -- .", "git clean -fd",
                "cp /tmp/x src/bug.test.ts", "echo x > src/bug.test.ts", "sed -i '' 's/a/b/' src/bug.test.ts"]:
        assert hook(r, "Bash", command=cmd) == 2, cmd


def test_unlock_asks_the_user():
    r = locked_repo()
    payload = json.dumps({"tool_name": "Bash", "cwd": r, "tool_input": {"command": f"bash {LOCKER} unlock"}})
    out = subprocess.run([HOOK], input=payload, capture_output=True, text=True)
    assert out.returncode == 0 and json.loads(out.stdout)["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_other_bash_is_allowed():
    r = locked_repo()
    for cmd in ["pnpm test src/bug.test.ts", "git checkout -b fix/x", "rm src/app.ts", "cat src/bug.test.ts",
                f"bash {LOCKER} check", f"bash {LOCKER} unlock", "git status"]:
        assert hook(r, "Bash", command=cmd) == 0, cmd


def test_check_detects_change_and_missing():
    r = locked_repo()
    out = locker(r, "check")
    assert out.returncode == 0 and "lock intact" in out.stdout
    with open(os.path.join(r, "src/bug.test.ts"), "w") as f:
        f.write("edited\n")
    out = locker(r, "check")
    assert out.returncode == 2 and "src/bug.test.ts" in out.stderr
    os.remove(os.path.join(r, "src/bug.test.ts"))
    assert "missing" in locker(r, "check").stderr


def test_lock_works_from_a_subdirectory_and_validates_input():
    r = repo()
    assert locker(os.path.join(r, "src"), "lock", "bug.test.ts").returncode == 0
    lock = json.load(open(os.path.join(r, ".git", "claude-fix-lock.json")))
    assert lock["files"][0]["path"] == "src/bug.test.ts" and "locked" in lock
    assert locker(r, "lock", "src/nope.ts").returncode == 2
    assert locker(r, "lock").returncode == 2
    assert locker(r, "bogus").returncode == 2


def test_no_lock_allows_everything():
    r = repo()
    assert hook(r, "Edit", file_path=os.path.join(r, "src/bug.test.ts")) == 0
    for cmd in ["git checkout -- src/bug.test.ts", "rm .git/claude-fix-lock.json", "git stash"]:
        assert hook(r, "Bash", command=cmd) == 0, cmd
    out = locker(r, "check")
    assert out.returncode == 0 and "no lock" in out.stdout
    assert hook(tempfile.mkdtemp(), "Edit", file_path="x.ts") == 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_test_lock: {len(tests)} passed")
