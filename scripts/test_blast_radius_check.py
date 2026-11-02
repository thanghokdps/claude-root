#!/usr/bin/env python3
"""Tests for plugins/guards/hooks/blast-radius-check.sh. Run: python3 scripts/test_blast_radius_check.py

The hook finds the repo from the event's cwd (falling back to its process cwd), then git rev-parse."""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "guards", "hooks", "blast-radius-check.sh")


def write(path, name, text=""):
    full = os.path.join(path, name)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(text)


def repo(declared="src/app.ts, src/util.ts", plan=True):
    path = tempfile.mkdtemp(prefix="blast-")
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    if plan:
        write(path, "specs/x/PLAN.md", f"status: active\n<task><files>{declared}</files></task>\n")
    return path


def run(cwd, rel, strict=False, tool="Edit"):
    if not os.path.exists(os.path.join(cwd, rel)):
        write(cwd, rel)  # the hook resolves symlinks (/var -> /private/var) only for files that exist
    event = {"hook_event_name": "PostToolUse", "tool_name": tool, "cwd": cwd,
             "tool_input": {"file_path": os.path.join(cwd, rel)}}
    env = {**os.environ}
    env.pop("BLAST_RADIUS_STRICT", None)
    if strict:
        env["BLAST_RADIUS_STRICT"] = "1"
    return subprocess.run([HOOK], input=json.dumps(event), capture_output=True, text=True, env=env, cwd=cwd)


def test_empty_input_is_a_noop():
    r = subprocess.run([HOOK], input="{}", capture_output=True, text=True, cwd=repo())
    assert r.returncode == 0 and r.stdout == ""


def test_in_scope_and_bookkeeping_files_pass():
    r = repo()
    for rel in ["src/app.ts", "lib/src/util.ts", "README.md", "docs/a.ts", "specs/x/PLAN.md"]:
        out = run(r, rel, strict=True)
        assert out.returncode == 0 and out.stdout == "", rel


def test_no_plan_or_no_files_tag_passes():
    assert run(repo(plan=False), "src/other.ts", strict=True).returncode == 0
    r = repo()
    write(r, "specs/x/PLAN.md", "status: active\nno files tag\n")
    assert run(r, "src/other.ts", strict=True).returncode == 0


def test_out_of_scope_edit_warns_with_context_by_default():
    out = run(repo(), "src/other.ts")
    assert out.returncode == 0
    ctx = json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "src/other.ts" in ctx and "NOT in the active plan" in ctx and "specs/x/PLAN.md" in ctx


def test_strict_mode_blocks_out_of_scope_edit():
    out = run(repo(), "src/other.ts", strict=True)
    assert out.returncode == 2
    assert "[BLAST RADIUS] src/other.ts is outside the active plan's <files> set." in out.stderr


def test_follows_the_repo_the_hook_runs_in():
    a, b = repo("src/app.ts"), repo("src/other.ts")
    assert run(a, "src/other.ts", strict=True).returncode == 2
    assert run(b, "src/other.ts", strict=True).returncode == 0
    nowhere = tempfile.mkdtemp(prefix="norepo-")
    assert run(nowhere, "src/other.ts", strict=True).returncode == 0


def test_new_file_under_docs_is_bookkeeping_even_when_absent():
    r = repo()
    event = {"hook_event_name": "PostToolUse", "tool_name": "Write", "cwd": r,
             "tool_input": {"file_path": os.path.join(r, "docs", "new", "guide.ts")}}
    assert not os.path.exists(event["tool_input"]["file_path"])
    out = subprocess.run([HOOK], input=json.dumps(event), capture_output=True, text=True,
                         env={**os.environ, "BLAST_RADIUS_STRICT": "1"}, cwd=r)
    assert out.returncode == 0 and out.stdout == ""


def test_event_cwd_beats_an_unrelated_process_cwd():
    r, elsewhere = repo("src/app.ts"), tempfile.mkdtemp(prefix="blast-else-")
    write(r, "src/other.ts")
    event = {"hook_event_name": "PostToolUse", "tool_name": "Edit", "cwd": r,
             "tool_input": {"file_path": os.path.join(r, "src/other.ts")}}
    out = subprocess.run([HOOK], input=json.dumps(event), capture_output=True, text=True,
                         env={**os.environ, "BLAST_RADIUS_STRICT": "1"}, cwd=elsewhere)
    assert out.returncode == 2 and "src/other.ts is outside" in out.stderr


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
