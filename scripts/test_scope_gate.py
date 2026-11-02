#!/usr/bin/env python3
"""Tests for plugins/guards/hooks/scope-gate.sh. Run: python3 scripts/test_scope_gate.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "guards", "hooks", "scope-gate.sh")


def run(payload, raw=None, cwd=None):
    data = raw if raw is not None else json.dumps(payload)
    return subprocess.run(["bash", HOOK], input=data, capture_output=True, text=True, cwd=cwd)


def context(r):
    return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


def test_empty_input_is_a_noop():
    r = run(None, raw="{}")
    assert r.returncode == 0 and r.stdout == ""


def test_question_short_and_skill_prompts_stay_silent():
    for prompt in ["how do I add a login page to the app", "fix it", "/ticket 412 add the login page now"]:
        r = run({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
        assert r.returncode == 0 and r.stdout == "", prompt


def test_shell_input_and_questions_in_any_language_stay_silent():
    for prompt in ["<bash-input>git -C /repo branch -D fix/kit-audit-drift</bash-input>",
                   "!git branch -D fix/old-branch now", "is there nothing left to improve in the kit?",
                   "không còn gì để improve nữa hả", "fix này đã merge chưa", "có cần update docs không"]:
        r = run({"hook_event_name": "UserPromptSubmit", "prompt": prompt})
        assert r.returncode == 0 and r.stdout == "", prompt


def test_implementation_prompt_gets_coordinator_context():
    r = run({"hook_event_name": "UserPromptSubmit", "prompt": "add a button to the settings page"})
    assert r.returncode == 0
    assert context(r).startswith("AUTO-COORDINATOR: implementation intent detected")
    assert "no high-risk keyword matched" in context(r)
    assert json.loads(r.stdout)["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"


def test_risk_keyword_is_named():
    r = run({"prompt": "refactor the password reset flow please"})
    assert r.returncode == 0
    assert 'high-risk keyword "password" matched' in context(r)


def test_output_follows_the_event_not_the_process_cwd():
    # The hook reads only .prompt; a different event cwd or process cwd changes nothing.
    other = os.path.join(ROOT, "scripts")
    r = run({"cwd": "/nonexistent", "prompt": "build the export feature now"}, cwd=other)
    assert r.returncode == 0 and "AUTO-COORDINATOR" in context(r)


def test_event_cwd_is_accepted_from_an_unrelated_process_cwd():
    fixture, elsewhere = tempfile.mkdtemp(prefix="scope-fixture-"), tempfile.mkdtemp(prefix="scope-else-")
    r = run({"cwd": fixture, "prompt": "refactor the password reset flow please"}, cwd=elsewhere)
    assert r.returncode == 0 and 'high-risk keyword "password" matched' in context(r)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
