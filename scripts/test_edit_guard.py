#!/usr/bin/env python3
"""Tests for plugins/core/hooks/edit-guard.sh. Run: python3 scripts/test_edit_guard.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "core", "hooks", "edit-guard.sh")


def repo():
    path = tempfile.mkdtemp(prefix="edit-guard-")
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    with open(os.path.join(path, ".gitignore"), "w") as f:
        f.write("logs/\n*.log\n")
    os.makedirs(os.path.join(path, "src"))
    return path


def code(command, cwd=None):
    cwd = cwd or repo()
    payload = json.dumps({"tool_name": "Bash", "cwd": cwd, "tool_input": {"command": command}})
    return subprocess.run([HOOK], input=payload, capture_output=True, text=True).returncode


def test_in_place_edits_are_blocked():
    for cmd in ["sed -i 's/a/b/' src/app.ts", "sed -i '' -e 's/a/b/' src/app.ts", "perl -pi -e 's/a/b/' src/x.py",
                "sed --in-place 's/a/b/' README.md"]:
        assert code(cmd) == 2, cmd


def test_writes_into_the_repo_are_blocked():
    for cmd in ["cat > src/app.ts <<'EOF'\nexport {}\nEOF", "echo x >> README.md", "printf x | tee src/a.ts",
                "cat <<EOF > src/b.ts\nx\nEOF"]:
        assert code(cmd) == 2, cmd


def test_inline_scripts_that_write_repo_files_are_blocked():
    cmd = "python3 - <<'PY'\nopen('src/app.ts','w').write('x')\nPY"
    assert code(cmd) == 2
    assert code("node -e \"require('fs').writeFileSync('src/a.ts','x')\"") == 2


def test_reads_scratch_and_ignored_targets_are_allowed():
    scratch = tempfile.mkdtemp()
    for cmd in ["grep -rn 'x > y' src", "cat src/app.ts", "pnpm test > logs/test.txt 2>&1", "pnpm lint > out.log",
                f"echo x > {scratch}/note.md", "ls > /dev/null", "git commit -m \"feat: a > b\"",
                "echo done >&2", "python3 scripts/gen.py", f"python3 - <<'PY'\nopen('{scratch}/a.txt','w')\nPY",
                "sed -n 1,20p src/app.ts", "git log --oneline > .git/notes.txt"]:
        assert code(cmd) == 0, cmd


def test_inline_script_judged_by_its_write_targets_not_its_data():
    # repo-audit writes its ledger to gitignored specs/; the tracked paths it mentions are data, not targets
    data = "rows = ['src/app.ts', 'README.md']\n"
    allowed = f"python3 - <<'PY'\n{data}open('logs/ledger.json', 'w').write(str(rows))\nPY"
    assert code(allowed) == 0
    tracked = f"python3 - <<'PY'\n{data}open('logs/ledger.json', 'w')\nopen('src/b.ts', 'w')\nPY"
    assert code(tracked) == 2
    unknown = f"python3 - <<'PY'\n{data}p = rows[0]\nopen(p, 'w').write('x')\nPY"
    assert code(unknown) == 2


def test_outside_a_git_repo_nothing_is_blocked():
    assert code("sed -i 's/a/b/' x.ts", cwd=tempfile.mkdtemp()) == 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_edit_guard: {len(tests)} passed")
