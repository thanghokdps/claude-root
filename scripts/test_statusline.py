#!/usr/bin/env python3
"""Tests for plugins/core/scripts/statusline.sh. Run: python3 scripts/test_statusline.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "core", "scripts", "statusline.sh")

PLAN = """Status: active
<task id="t1" status="done"><action>first thing</action></task>
<task id="t2"><action>second thing</action></task>
"""


def git(path, *a):
    return subprocess.run(["git", "-C", path, "-c", "user.name=t", "-c", "user.email=t@t", *a],
                          check=True, capture_output=True, text=True).stdout.strip()


def repo(branch):
    d = tempfile.mkdtemp(prefix="statusline-")
    git(d, "init", "-q", "-b", "main")
    git(d, "commit", "-q", "--allow-empty", "-m", "init")
    git(d, "checkout", "-q", "-b", branch)
    return d


def run(payload):
    p = subprocess.run(["bash", SCRIPT], input=payload if isinstance(payload, str) else json.dumps(payload),
                       capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def test_empty_json_exits_zero():
    assert run("{}")[0] == 0
    assert run("")[0] == 0
    assert run("not json")[0] == 0


def test_branch_ticket_and_plan_slice():
    d = repo("feat/412-x")
    os.makedirs(os.path.join(d, "specs", "412"))
    with open(os.path.join(d, "specs", "412", "PLAN.md"), "w") as f:
        f.write(PLAN)
    code, out = run({"model": {"display_name": "Opus"}, "workspace": {"current_dir": d}})
    assert code == 0, out
    assert out == "Opus · feat/412-x #412 · plan 1/2 second thing", out


def test_context_figure_matches_input():
    d = repo("feat/412-x")
    _, out = run({"workspace": {"current_dir": d}, "context_window": {"used_percentage": 42.9}})
    assert out.endswith("ctx 42%") and "\033" not in out, out
    _, out = run({"workspace": {"current_dir": d},
                  "context_window": {"total_input_tokens": 50_000, "context_window_size": 200_000}})
    assert out.endswith("ctx 25%"), out
    _, out = run({"workspace": {"current_dir": d}, "context_window": {"used_percentage": 90}})
    assert "\033[31mctx 90%" in out, repr(out)


def test_no_crash_outside_a_repo():
    d = tempfile.mkdtemp(prefix="statusline-norepo-")
    code, out = run({"model": {"display_name": "Opus"}, "workspace": {"current_dir": d},
                     "context_window": {"used_percentage": 10}})
    assert code == 0 and out == "Opus · ctx 10%", out


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    for name, t in tests:
        t()
        print(f"ok {name}")
    print(f"test_statusline: {len(tests)} passed")
