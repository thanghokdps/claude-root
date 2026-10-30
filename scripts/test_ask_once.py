#!/usr/bin/env python3
"""Tests for plugins/dev/hooks/ask-once.sh. Run: python3 scripts/test_ask_once.py"""
import json
import os
import subprocess
import tempfile
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "dev", "hooks", "ask-once.sh")
TMP = tempfile.mkdtemp(prefix="ask-once-")


def run(sid, event, tool=None, tool_input=None):
    payload = {"session_id": sid, "hook_event_name": event}
    if tool:
        payload["tool_name"] = tool
        payload["tool_input"] = tool_input or {}
    out = subprocess.run([HOOK], input=json.dumps(payload), capture_output=True, text=True,
                         env={**os.environ, "TMPDIR": TMP})
    assert out.returncode == 0, out.stderr
    return out.stdout.strip()


def edit(sid, path):
    return run(sid, "PostToolUse", "Edit", {"file_path": path})


def ask(sid):
    out = run(sid, "PreToolUse", "AskUserQuestion", {"questions": []})
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else "allow"


def session():
    sid = uuid.uuid4().hex
    run(sid, "UserPromptSubmit")
    return sid


def test_question_before_any_edit_passes():
    assert ask(session()) == "allow"


def test_plan_and_spec_edits_do_not_start_the_build():
    sid = session()
    for path in ("/r/specs/x/PLAN.md", "/r/docs/tickets/412/plan.md", "/Users/u/.claude/plans/p.md",
                 "/r/docs/features/cancel-order.md", "/r/docs/adr/0002-writes.md"):
        edit(sid, path)
    assert ask(sid) == "allow"


def test_first_question_after_a_code_edit_is_denied_then_the_retry_passes():
    sid = session()
    edit(sid, "/r/src/app.ts")
    assert ask(sid) == "deny"
    assert ask(sid) == "allow"


def test_new_prompt_resets_the_build():
    sid = session()
    edit(sid, "/r/src/app.ts")
    run(sid, "UserPromptSubmit")
    assert ask(sid) == "allow"


def test_reason_points_at_the_debate():
    sid = session()
    edit(sid, "/r/src/app.ts")
    out = run(sid, "PreToolUse", "AskUserQuestion", {"questions": []})
    assert "/resolve-question" in json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]


def transcript(*texts):
    path = os.path.join(TMP, uuid.uuid4().hex + ".jsonl")
    with open(path, "w") as f:
        f.write(json.dumps({"type": "user", "message": {"content": "build it"}}) + "\n")
        for t in texts:
            f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": t}]}}) + "\n")
    return path


def stop(sid, path, active=False):
    out = subprocess.run([HOOK], input=json.dumps({"session_id": sid, "hook_event_name": "Stop",
                                                   "transcript_path": path, "stop_hook_active": active}),
                         capture_output=True, text=True, env={**os.environ, "TMPDIR": TMP})
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)["decision"] if out.stdout.strip() else "allow"


def test_reply_ending_in_a_question_after_a_code_edit_is_blocked_once():
    sid = session()
    edit(sid, "/r/src/app.ts")
    path = transcript("Done: 3 tests pass.\n\nShould the error message be translated too?")
    assert stop(sid, path) == "block"
    assert stop(sid, path, active=True) == "allow"


def test_bold_trailing_question_counts():
    sid = session()
    edit(sid, "/r/src/app.ts")
    assert stop(sid, transcript("**Which rounding do you want?**")) == "block"


def test_reply_without_a_question_or_before_the_build_ends():
    sid = session()
    assert stop(sid, transcript("Before I start: which layout?")) == "allow"
    edit(sid, "/r/src/app.ts")
    assert stop(sid, transcript("Is this right? Yes.\n\nAll 3 tests pass.")) == "allow"
    assert stop(sid, os.path.join(TMP, "missing.jsonl")) == "allow"


def test_bad_input_and_other_tools_exit_clean():
    out = subprocess.run([HOOK], input="not json", capture_output=True, text=True)
    assert out.returncode == 0 and not out.stdout
    sid = session()
    edit(sid, "/r/src/app.ts")
    assert run(sid, "PreToolUse", "Bash", {"command": "ls"}) == ""
    assert run("../x", "PreToolUse", "AskUserQuestion") == ""


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_ask_once: {len(tests)} passed")
