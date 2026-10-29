#!/usr/bin/env python3
"""Tests for plugins/dev/hooks/weakened-check.sh. Run: python3 scripts/test_weakened_check.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "dev", "hooks", "weakened-check.sh")

BASE = {
    "src/app.ts": "export const a = 1;\n",
    "src/app.test.ts": "test('a', () => {\n  expect(a).toBe(1);\n  expect(b).toBe(2);\n});\n",
    "tests/test_app.py": "def test_a():\n    assert a == 1\n",
    "jest.config.js": "module.exports = { coverageThreshold: { global: { lines: 80 } } };\n",
    "pyproject.toml": "[tool.coverage.report]\nfail_under = 90\n",
    "package.json": '{ "scripts": { "lint": "eslint . --max-warnings 5" } }\n',
}


def git(cwd, *args):
    subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True)


def write(r, name, text):
    os.makedirs(os.path.dirname(os.path.join(r, name)), exist_ok=True)
    with open(os.path.join(r, name), "w") as f:
        f.write(text)


def repo():
    r = tempfile.mkdtemp(prefix="weakened-check-")
    git(r, "init", "-q")
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "t")
    for name, text in BASE.items():
        write(r, name, text)
    git(r, "add", "-A")
    git(r, "commit", "-qm", "base")
    return r


def staged(r, name, text):
    write(r, name, text)
    git(r, "add", name)


def hook(cwd, command="git commit -m x"):
    payload = json.dumps({"tool_name": "Bash", "cwd": cwd, "tool_input": {"command": command}})
    out = subprocess.run([HOOK], input=payload, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return out.stdout


def reason(out):
    hso = json.loads(out)["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse" and hso["permissionDecision"] == "ask"
    return hso["permissionDecisionReason"]


def test_each_added_suppression_asks():
    for line in ["// eslint-disable-next-line no-console", "// @ts-ignore", "// @ts-nocheck",
                 "// @ts-expect-error", "// biome-ignore lint: x", "x = 1  # noqa", "x = f()  # type: ignore",
                 "/* istanbul ignore next */", "// nosemgrep"]:
        r = repo()
        staged(r, "src/app.ts", BASE["src/app.ts"] + line + "\n")
        text = reason(hook(r))
        assert "suppression" in text and "src/app.ts:2" in text, (line, text)


def test_each_added_skip_asks():
    for line in ["test.skip('b', () => {});", "describe.only('b', () => {});", "xit('b', () => {});",
                 "xdescribe('b', () => {});", "@pytest.mark.skip(reason='flaky')", "t.Skip(\"later\")"]:
        r = repo()
        staged(r, "src/app.ts", BASE["src/app.ts"] + line + "\n")
        assert "skip" in reason(hook(r)), line


def test_deleted_test_file_asks():
    r = repo()
    git(r, "rm", "-q", "src/app.test.ts")
    text = reason(hook(r))
    assert "test-deleted" in text and "src/app.test.ts" in text


def test_removed_assertion_in_a_kept_test_asks():
    r = repo()
    staged(r, "src/app.test.ts", BASE["src/app.test.ts"].replace("  expect(b).toBe(2);\n", ""))
    text = reason(hook(r))
    assert "assertion-removed" in text and "src/app.test.ts:3" in text
    r = repo()
    staged(r, "tests/test_app.py", "def test_a():\n    pass\n")
    assert "tests/test_app.py:2" in reason(hook(r))


def test_lowered_threshold_asks():
    for name, old, new in [("jest.config.js", "lines: 80", "lines: 60"),
                           ("pyproject.toml", "fail_under = 90", "fail_under = 70"),
                           ("package.json", "--max-warnings 5", "--max-warnings 20")]:
        r = repo()
        staged(r, name, BASE[name].replace(old, new))
        text = reason(hook(r))
        assert "threshold-loosened" in text and name in text, name
    r = repo()
    write(r, "setup.cfg", "addopts = --cov-fail-under=85\n")
    git(r, "add", "setup.cfg")
    git(r, "commit", "-qm", "cov")
    staged(r, "setup.cfg", "addopts = --cov-fail-under=50\n")
    assert "threshold-loosened" in reason(hook(r))


def test_raised_threshold_and_added_assertion_are_silent():
    for name, old, new in [("jest.config.js", "lines: 80", "lines: 95"),
                           ("pyproject.toml", "fail_under = 90", "fail_under = 95"),
                           ("package.json", "--max-warnings 5", "--max-warnings 0")]:
        r = repo()
        staged(r, name, BASE[name].replace(old, new))
        assert hook(r) == "", name
    r = repo()
    staged(r, "src/app.test.ts", BASE["src/app.test.ts"].replace("toBe(2)", "toBe(2);\n  expect(c).toBe(3)"))
    assert hook(r) == ""


def test_clean_commit_gives_no_output():
    r = repo()
    staged(r, "src/app.ts", "export const a = 2;\n")
    assert hook(r) == ""
    assert hook(r, "git commit -am 'fix'") == ""


def test_commit_all_reads_unstaged_tracked_changes():
    r = repo()
    write(r, "src/app.ts", BASE["src/app.ts"] + "// @ts-ignore\n")
    assert hook(r) == ""
    assert "suppression" in reason(hook(r, "git commit -am x"))
    assert "suppression" in reason(hook(os.path.dirname(r), f"git -C {r} commit -a -m x"))


def test_repo_config_cannot_run_commands_before_approval():
    r = repo()
    pwned = os.path.join(r, "PWNED")
    git(r, "config", "core.fsmonitor", f"touch {pwned}; false")
    for name in ("evil", "a.b"):
        for key in ("clean", "process", "smudge"):
            git(r, "config", f"filter.{name}.{key}", f"touch {pwned}")
        git(r, "config", f"filter.{name}.required", "true")
    write(r, ".gitattributes", "*.ts filter=evil\n*.py filter=a.b\n")
    write(r, "src/app.ts", BASE["src/app.ts"] + "// @ts-ignore\n")
    write(r, "tests/test_app.py", BASE["tests/test_app.py"] + "x = 1  # noqa\n")
    text = reason(hook(r, "git commit -am x"))
    assert not os.path.exists(pwned)
    assert "src/app.ts:2" in text and "tests/test_app.py:3" in text


def test_crafted_filter_driver_names_cannot_inject_an_override():
    r = repo()
    pwned = os.path.join(r, "PWNED")
    # `=` in the name: a `-c filter.<name>.clean=` override would set filter.inj.clean to a command.
    git(r, "config", f"filter.inj.clean=touch {pwned} #.clean", "x")
    # `.clean ` in the value: a plain --get-regexp line would read part of it as the name.
    git(r, "config", "filter.v.clean", f"touch {pwned} .clean x")
    write(r, ".gitattributes", "*.json filter=inj\n*.toml filter=v\n")
    write(r, "package.json", BASE["package.json"].replace("5", "20"))
    write(r, "pyproject.toml", BASE["pyproject.toml"].replace("90", "70"))
    hook(r, "git commit -am x")
    assert not os.path.exists(pwned)


def test_submodules_are_not_diffed_inside():
    sub = repo()
    write(sub, ".gitattributes", "*.ts filter=s\n")
    git(sub, "add", ".gitattributes")
    git(sub, "commit", "-qm", "attrs")
    r = repo()
    git(r, "-c", "protocol.file.allow=always", "submodule", "add", "-q", sub, "vendor/sub")
    git(r, "commit", "-qm", "sub")
    pwned = os.path.join(r, "PWNED")
    git(os.path.join(r, "vendor/sub"), "config", "filter.s.clean", f"touch {pwned}")
    git(r, "config", "diff.submodule", "diff")
    write(os.path.join(r, "vendor/sub"), "src/app.ts", BASE["src/app.ts"] + "// @ts-ignore\n")
    write(r, "src/app.ts", BASE["src/app.ts"] + "// @ts-ignore\n")
    assert "src/app.ts:2" in reason(hook(r, "git commit -am x"))
    assert not os.path.exists(pwned)


def test_non_commit_commands_are_ignored():
    r = repo()
    staged(r, "src/app.ts", BASE["src/app.ts"] + "// @ts-ignore\n")
    for cmd in ["git status", "git diff --cached", "echo git commit", "git log --grep commit", "pnpm test"]:
        assert hook(r, cmd) == "", cmd
    payload = json.dumps({"tool_name": "Edit", "cwd": r, "tool_input": {"file_path": "src/app.ts"}})
    assert subprocess.run([HOOK], input=payload, capture_output=True, text=True).stdout == ""


def test_no_repo_or_nothing_staged_exits_clean():
    assert hook(tempfile.mkdtemp()) == ""
    assert hook(repo()) == ""
    assert subprocess.run([HOOK], input="not json", capture_output=True, text=True).returncode == 0


def test_reason_truncates_and_hides_secret_values():
    r = repo()
    secret = "sk_live_" + "A1b2C3d4" * 6
    staged(r, "src/app.ts", BASE["src/app.ts"] + f"const key = '{secret}'; // eslint-disable-line {'x' * 300}\n")
    text = reason(hook(r))
    assert secret not in text and "A1b2C3d4A1b2" not in text and len(text) < 600


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_weakened_check: {len(tests)} passed")
