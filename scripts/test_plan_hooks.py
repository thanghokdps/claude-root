#!/usr/bin/env python3
"""Tests for plugins/dev/hooks/plan-recall.sh and plan-gate.sh. Run: python3 scripts/test_plan_hooks.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECALL = os.path.join(ROOT, "plugins", "dev", "hooks", "plan-recall.sh")
GATE = os.path.join(ROOT, "plugins", "dev", "hooks", "plan-gate.sh")

PLAN = """# Plan — pin chat

**Goal:** pin a chat
**Status:** {status}

## Tasks

```xml
<task id="1.1" wave="1" status="done">
  <files>src/pin.ts</files>
  <action>Add the pin model</action>
  <verify>npm test -- pin</verify>
  <done>pin tests pass</done>
</task>

<task id="1.2" wave="1">
  <files>src/api.ts</files>
  <action>Expose POST /chats/:id/pin
    and the unpin route</action>
  <verify>npm test -- api</verify>
  <done>api tests pass</done>
</task>
```

## Status log

- 2026-10-01 draft created
- 2026-10-02 active
- 2026-10-03 task 1.1 done
- 2026-10-04 started 1.2
"""


def repo(status="active", slug="pin-chat", plan=PLAN):
    path = tempfile.mkdtemp(prefix="plan-hooks-")
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    os.makedirs(os.path.join(path, "specs", slug))
    with open(os.path.join(path, "specs", slug, "PLAN.md"), "w") as f:
        f.write(plan.format(status=status))
    return path


def run(hook, payload):
    r = subprocess.run([hook], input=payload if isinstance(payload, str) else json.dumps(payload),
                       capture_output=True, text=True, env={**os.environ, "TMPDIR": tempfile.mkdtemp()})
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def recall(path):
    out = run(RECALL, {"session_id": "t1", "hook_event_name": "UserPromptSubmit", "cwd": path})
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


def gate(path, active=False):
    out = run(GATE, {"session_id": "t1", "hook_event_name": "Stop", "cwd": path, "stop_hook_active": active})
    return json.loads(out) if out else {}


def test_recall_prints_the_slice_of_an_active_plan():
    ctx = recall(repo())
    assert "specs/pin-chat/PLAN.md" in ctx and "(1/2 tasks done)" in ctx
    assert "task 1.2 'Expose POST /chats/:id/pin and the unpin route'" in ctx
    assert "- 2026-10-02 active" in ctx and "- 2026-10-04 started 1.2" in ctx and "draft created" not in ctx
    assert len(ctx) <= 1600


def test_recall_from_a_subdirectory_finds_the_git_toplevel():
    path = repo()
    os.makedirs(os.path.join(path, "src"))
    assert "specs/pin-chat/PLAN.md" in recall(os.path.join(path, "src"))


def test_recall_is_silent_for_paused_draft_and_complete_plans():
    for status in ("paused", "draft", "complete"):
        assert recall(repo(status)) == "", status


def test_recall_caps_at_two_plans():
    path = repo()
    for slug in ("b-plan", "c-plan"):
        os.makedirs(os.path.join(path, "specs", slug))
        with open(os.path.join(path, "specs", slug, "PLAN.md"), "w") as f:
            f.write(PLAN.format(status="active"))
    assert recall(path).count("Active plan ") == 2


def test_recall_says_when_every_task_is_done():
    ctx = recall(repo(plan=PLAN.replace('<task id="1.2" wave="1">', '<task id="1.2" wave="1" status="done">')))
    assert "every task is done: set **Status:** complete" in ctx


def test_gate_blocks_once_then_the_retry_passes():
    path = repo()
    first = gate(path)
    assert first["decision"] == "block"
    assert "PLAN specs/pin-chat/PLAN.md: task 1.2 'Expose POST /chats/:id/pin and the unpin route' not done" in first["reason"]
    assert "paused" in first["reason"]
    assert gate(path, active=True) == {}


def test_gate_never_blocks_a_paused_complete_or_finished_plan():
    assert gate(repo("paused")) == {}
    assert gate(repo("complete")) == {}
    assert gate(repo(plan=PLAN.replace('<task id="1.2" wave="1">', '<task id="1.2" wave="1" status="done">'))) == {}


def test_empty_payload_and_no_plan_exit_quietly():
    for hook in (RECALL, GATE):
        assert run(hook, "{}") == ""
        assert run(hook, "not json") == ""
        assert run(hook, {"cwd": tempfile.mkdtemp()}) == ""


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_plan_hooks: {len(tests)} passed")
