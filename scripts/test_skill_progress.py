#!/usr/bin/env python3
"""Tests for plugins/progress/hooks/skill-progress.sh. Run: python3 scripts/test_skill_progress.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugins", "progress")
HOOK = os.path.join(PLUGIN, "hooks", "skill-progress.sh")
DATA = tempfile.mkdtemp(prefix="skill-progress-")


def run(payload):
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": PLUGIN, "CLAUDE_PLUGIN_DATA": DATA}
    r = subprocess.run([HOOK], input=raw, capture_output=True, text=True, env=env)
    assert r.returncode == 0, (r.returncode, r.stderr)  # exit 2 on TaskCompleted would refuse the completion
    return json.loads(r.stdout) if r.stdout.strip() else None


def invoke(session, skill="agent:agent-tool"):
    return run({"hook_event_name": "PostToolUse", "session_id": session, "tool_input": {"skill": skill}})


def stop(session, reply=""):
    out = run({"hook_event_name": "Stop", "session_id": session, "last_assistant_message": reply})
    return out and out["systemMessage"]


def test_invocation_injects_checklist_with_done_when():
    out = invoke("inject")
    assert out["systemMessage"].startswith("📋 /agent-tool — 5 checkpoints: From an API the user provides")
    ctx = out["hookSpecificOutput"]["additionalContext"]
    assert "- [ ] Step 2 — Contract first — done when:" in ctx and "TaskCreate" in ctx and "⏭" in ctx


def test_same_invocation_from_both_events_is_injected_once():
    invoke("dedupe")
    assert run({"hook_event_name": "UserPromptExpansion", "session_id": "dedupe",
                "command_name": "agent:agent-tool"}) is None


def test_skill_without_steps_and_bad_input_stay_silent():
    assert invoke("none", "btw") is None
    assert invoke("none", "no-such-skill") is None
    assert run("not json") is None


def test_task_tools_count_each_completion_then_complete():
    for i in ("1", "2"):
        run({"hook_event_name": "TaskCreated", "session_id": "tasks", "task_id": i, "task_subject": f"S{i}"})
    assert run({"hook_event_name": "TaskCompleted", "session_id": "tasks", "task_id": "1",
                "task_subject": "S1"})["systemMessage"] == "✅ (1/2) S1"
    run({"hook_event_name": "TaskCompleted", "session_id": "tasks", "task_id": "2", "task_subject": "S2"})
    assert stop("tasks") == "🏁 Checklist complete — 2/2"
    assert stop("tasks") is None  # unchanged → quiet


def test_markers_count_done_and_report_open_steps():
    invoke("markers")
    assert stop("markers", "reading the repo…") is None
    assert stop("markers", "✅ Step 0 — From an API the user provides").startswith("⏳ 1/5 done — open: Step 1")
    assert stop("markers", "✅ Step 1 — Detect and place\n- ✅ Contract first\n**✅ Step 3 — Implement**\n"
                           "✅ Step 4 — Prove it in a turn") == "🏁 Checklist complete — 5/5 for /agent-tool"


def test_skipped_steps_never_read_as_complete():
    invoke("skipped")
    msg = stop("skipped", "⏭ Step 0 — From an API the user provides\n⏭ Step 1 — Detect and place\n⏭️ Step 2 — Contract first\n⏭ Step 3 — Implement\n"
                          "⏭ Step 4 — Prove it in a turn")
    assert msg == "⏹ Checklist closed for /agent-tool — ✅ 0 done · ⏭ 5 skipped", msg


def test_short_marker_matches_no_step():
    invoke("short")
    assert stop("short", "✅ ok") is None


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_skill_progress: {len(tests)} passed")
