#!/usr/bin/env python3
"""Tests for plugins/guards/hooks/session-handoff.sh. Run: python3 scripts/test_session_handoff.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "guards", "hooks", "session-handoff.sh")


def repo():
    path = tempfile.mkdtemp(prefix="handoff-")
    subprocess.run(["git", "-C", path, "init", "-q", "-b", "feat/x"], check=True)
    with open(os.path.join(path, ".git", "info", "exclude"), "a") as f:
        f.write("specs/\n")  # as in the kit's projects, where specs/ is gitignored
    subprocess.run(["git", "-C", path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty",
                    "-m", "init"], check=True)
    return path


def spec(r, slug, status=None):
    d = os.path.join(r, "specs", slug)
    os.makedirs(d)
    with open(os.path.join(d, "SUMMARY.md"), "w") as f:
        f.write(f"# Summary — {slug}\n\nLane: normal\n")
    with open(os.path.join(d, "PLAN.md"), "w") as f:
        f.write(f"# Plan — {slug}\n\n" + (f"**Status:** {status}\n" if status else ""))


def handoff(r, **event):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": r}
    subprocess.run([HOOK], input=json.dumps({"cwd": r, **event}), capture_output=True, text=True, check=True, env=env)
    return open(os.path.join(r, "specs", "HANDOFF.md")).read()


def test_complete_specs_are_left_out_and_the_rest_show_their_status():
    r = repo()
    spec(r, "shipped", "complete")
    spec(r, "building", "active — wave 2")
    spec(r, "old")
    text = handoff(r)
    assert "shipped" not in text
    assert "building (normal, active — wave 2)" in text and "old (normal, no status)" in text


def test_next_steps_quote_the_last_reply():
    r = repo()
    text = handoff(r, last_assistant_message="PR #12 is open.\nNext: merge it, then run install.sh.")
    assert "Next: merge it, then run install.sh." in text
    assert "<!-- Agent: fill this in" not in text and "STATE.md" not in text


def test_next_steps_fall_back_to_the_transcript():
    r = repo()
    transcript = os.path.join(tempfile.mkdtemp(), "t.jsonl")
    with open(transcript, "w") as f:
        for role, text in [("user", "do it"), ("assistant", "old reply"), ("assistant", "Done: tests pass.")]:
            f.write(json.dumps({"type": role, "message": {"role": role, "content": [{"type": "text", "text": text}]}}) + "\n")
    text = handoff(r, transcript_path=transcript)
    assert "Done: tests pass." in text and "old reply" not in text


def test_git_state_and_reload_list_are_left_to_the_session():
    text = handoff(repo())
    assert "## Last commits" not in text and "## Git state" not in text and "## Context to reload" not in text
    assert "## Branch" in text and "## Where it stood" in text


def test_resume_injects_once_and_deletes_the_file():
    r = repo()
    handoff(r, last_assistant_message="Next: open the PR.")
    resume = os.path.join(ROOT, "plugins", "guards", "hooks", "session-resume.sh")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": r}
    out = subprocess.run([resume], input=json.dumps({"cwd": r}), capture_output=True, text=True, check=True, env=env)
    assert "Next: open the PR." in json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"]
    assert not os.path.exists(os.path.join(r, "specs", "HANDOFF.md"))


def resume(r, home):
    hook = os.path.join(ROOT, "plugins", "guards", "hooks", "session-resume.sh")
    env = {**os.environ, "CLAUDE_PROJECT_DIR": r, "HOME": home}
    return subprocess.run([hook], input=json.dumps({"cwd": r}), capture_output=True, text=True, check=True, env=env)


def test_resume_points_at_the_personal_index_without_a_handoff():
    r, home = repo(), tempfile.mkdtemp()
    promote = os.path.join(ROOT, "plugins", "core", "scripts", "learn-promote.py")
    folder = subprocess.run(["python3", promote, "--personal-dir"], cwd=r, capture_output=True, text=True,
                            check=True, env={**os.environ, "HOME": home}).stdout.strip()
    assert resume(r, home).stdout == ""  # nothing to point at yet
    os.makedirs(folder)
    open(os.path.join(folder, "INDEX.md"), "w").write("# Personal\n")
    context = json.loads(resume(r, home).stdout)["hookSpecificOutput"]["additionalContext"]
    assert os.path.join(folder, "INDEX.md") in context and "Previous session handoff" not in context


def test_a_long_reply_is_cut_to_its_tail():
    r = repo()
    text = handoff(r, last_assistant_message="\n".join(f"line {i}" for i in range(100)))
    assert "line 99" in text and "line 0\n" not in text


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_session_handoff: {len(tests)} passed")
