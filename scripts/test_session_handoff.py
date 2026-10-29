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
    subprocess.run([HOOK], input=json.dumps({"cwd": r, **event}), capture_output=True, text=True, check=True)
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


def test_a_long_reply_is_cut_to_its_tail():
    r = repo()
    text = handoff(r, last_assistant_message="\n".join(f"line {i}" for i in range(100)))
    assert "line 99" in text and "line 0\n" not in text


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_session_handoff: {len(tests)} passed")
