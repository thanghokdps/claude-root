#!/usr/bin/env python3
"""Tests for plugins/core/hooks/learn-capture.sh, with a fake `claude` on PATH.
Run: python3 scripts/test_learn_capture.py"""
import glob
import json
import os
import subprocess
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "core", "hooks", "learn-capture.sh")
TOOL_OUTPUT = "TOOL-OUTPUT-MUST-NOT-LEAK"
KEY = "sk-" + "a1B2c3D4e5F6g7H8i9J0k1L2m3"
FAKE = """#!/bin/sh
mkdir -p "$FAKE_CLAUDE_LOG"
cat > "$FAKE_CLAUDE_LOG/$$.stdin"
printf '%s\\n' "$@" > "$FAKE_CLAUDE_LOG/$$.argv"
printf '%s' "${HARNESS_LEARN_CHILD:-}" > "$FAKE_CLAUDE_LOG/$$.env"
printf '%s' "${FAKE_CLAUDE_REPLY:-}"
"""
LESSON = {"slug": "piped-test-exit-codes", "title": "Never pipe test output", "body": "Run tests unpiped.",
          "level": "global", "confidence": "high", "evidence": "Stop piping test output through tail."}


def setup():
    base = tempfile.mkdtemp(prefix="learn-capture-")
    repo = os.path.join(base, "repo")
    os.makedirs(repo)
    subprocess.run(["git", "-C", repo, "init", "-q"], check=True)
    fakebin = os.path.join(base, "bin")
    os.makedirs(fakebin)
    with open(os.path.join(fakebin, "claude"), "w") as f:
        f.write(FAKE)
    os.chmod(os.path.join(fakebin, "claude"), 0o755)
    transcript = os.path.join(base, "t.jsonl")
    write_transcript(transcript)
    env = {**os.environ, "PATH": fakebin + os.pathsep + os.environ["PATH"], "HOME": base,
           "FAKE_CLAUDE_LOG": os.path.join(base, "log")}
    for k in ("HARNESS_LEARN", "HARNESS_LEARN_CHILD"):
        env.pop(k, None)
    return {"repo": repo, "transcript": transcript, "env": env, "log": env["FAKE_CLAUDE_LOG"],
            "state": os.path.join(repo, ".git", "claude-learn")}


def write_transcript(path, filler=0):
    events = [
        {"type": "user", "message": {"role": "user", "content": "Stop piping test output through tail."}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "thinking", "thinking": "private reasoning"},
            {"type": "text", "text": "Running the tests without a pipe."},
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "pytest -q"}}]}},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": TOOL_OUTPUT}]}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": f"The key in the log was {KEY}, rotate it."}]}},
    ]
    events += [{"type": "user", "message": {"role": "user", "content": f"filler line {i} " + "x" * 200}}
                for i in range(filler)]
    with open(path, "w") as f:
        f.write("\n".join(json.dumps(e) for e in events) + "\n")


def hook(s, event, env=None, **extra):
    payload = json.dumps({"hook_event_name": event, "session_id": "sess-1", "cwd": s["repo"],
                          "transcript_path": s["transcript"], "tool_name": "Bash", "tool_input": {}, **extra})
    r = subprocess.run([HOOK], input=payload, capture_output=True, text=True, env={**s["env"], **(env or {})})
    assert r.returncode == 0, r.stderr
    return r


def calls(s, n, env=None):
    for _ in range(n):
        hook(s, "PreToolUse", env)


def spawns(s, expect, wait=5.0):
    """Spawn records once `expect` have appeared (or `wait` seconds passed)."""
    deadline = time.time() + wait
    while True:
        found = sorted(glob.glob(os.path.join(s["log"], "*.env")))
        if len(found) >= expect or time.time() > deadline:
            return found
        time.sleep(0.1)


def queued(s, expect, wait=5.0):
    """Queue files once `expect` have appeared (or `wait` seconds passed)."""
    deadline = time.time() + wait
    while True:
        found = sorted(glob.glob(os.path.join(s["state"], "queue", "*.json")))
        if len(found) >= expect or time.time() > deadline:
            return found
        time.sleep(0.1)


def read(path):
    with open(path) as f:
        return f.read()


def test_exactly_one_spawn_after_50_calls():
    s = setup()
    calls(s, 49)
    hook(s, "Stop")
    assert spawns(s, 1, wait=1.0) == []
    calls(s, 1)
    hook(s, "Stop")
    assert len(spawns(s, 1)) == 1
    assert read(os.path.join(s["state"], "sess-1.count")) == "0"
    hook(s, "Stop")
    found = spawns(s, 2, wait=1.0)
    assert len(found) == 1, found
    argv = read(found[0].replace(".env", ".argv")).split("\n")
    assert "-p" in argv and argv[argv.index("--model") + 1] == "haiku"
    # No tools: Claude Code refuses the child's writes under .git/, so the hook writes the queue itself.
    assert argv[argv.index("--tools") + 1] == ""
    assert "Write" not in argv and "--allowedTools" not in argv
    assert read(found[0]) == "1"  # the child runs with HARNESS_LEARN_CHILD=1


def test_reply_array_becomes_one_queue_file_per_lesson():
    s = setup()
    other = {**LESSON, "slug": "second-lesson"}
    reply = "Here they are:\n```json\n" + json.dumps([LESSON, other]) + "\n```"
    calls(s, 50)
    hook(s, "Stop", {"FAKE_CLAUDE_REPLY": reply})
    found = queued(s, 2)
    assert sorted(json.loads(read(f))["slug"] for f in found) == ["piped-test-exit-codes", "second-lesson"]
    assert all("/" not in os.path.basename(f)[:-5] for f in found)  # names never come from the reply


def test_empty_array_queues_nothing_and_garbage_is_queued_raw():
    s = setup()
    calls(s, 50)
    hook(s, "Stop", {"FAKE_CLAUDE_REPLY": "[]"})
    spawns(s, 1)
    assert queued(s, 1, wait=1.0) == []
    write_transcript(s["transcript"], filler=1)  # new text, so the next Stop reflects again
    calls(s, 50)
    hook(s, "Stop", {"FAKE_CLAUDE_REPLY": "I could not find any lessons."})
    found = queued(s, 1)
    assert len(found) == 1 and read(found[0]).strip() == "I could not find any lessons."


def test_recursion_guard_and_off_switch():
    for env in ({"HARNESS_LEARN_CHILD": "1"}, {"HARNESS_LEARN": "0"}):
        s = setup()
        calls(s, 55, env)
        hook(s, "Stop", env)
        assert not os.path.exists(os.path.join(s["state"], "sess-1.count")), env
        assert spawns(s, 1, wait=1.0) == [], env


def test_digest_has_text_and_tool_names_but_no_tool_output():
    s = setup()
    calls(s, 50)
    hook(s, "Stop")
    found = spawns(s, 1)
    assert len(found) == 1
    digest = read(glob.glob(os.path.join(s["state"], "digests", "*.txt"))[0])
    prompt = read(found[0].replace(".env", ".stdin"))
    for text in (digest, prompt):
        assert "Stop piping test output through tail." in text
        assert "[tool: Bash]" in text
        assert TOOL_OUTPUT not in text
        assert "pytest -q" not in text  # tool input is left out too
        assert "private reasoning" not in text


def test_planted_key_is_scrubbed():
    s = setup()
    calls(s, 50)
    hook(s, "Stop")
    found = spawns(s, 1)
    digest = read(glob.glob(os.path.join(s["state"], "digests", "*.txt"))[0])
    for text in (digest, read(found[0].replace(".env", ".stdin"))):
        assert KEY not in text and "sk-a1B2" not in text
    assert "[REDACTED]" in digest


def test_digest_is_capped_and_starts_after_the_last_reflection():
    s = setup()
    write_transcript(s["transcript"], filler=400)
    calls(s, 50)
    hook(s, "Stop")
    spawns(s, 1)
    digest = glob.glob(os.path.join(s["state"], "digests", "*.txt"))[0]
    assert os.path.getsize(digest) <= 20_480
    assert "filler line 399" in read(digest)  # the cap keeps the most recent text
    calls(s, 50)
    hook(s, "Stop")  # nothing new in the transcript since the last run: no spawn
    assert len(spawns(s, 2, wait=1.0)) == 1


def test_bad_input_never_fails():
    s = setup()
    for payload in ("", "not json", "{}", json.dumps({"hook_event_name": "Stop", "session_id": "../x"})):
        r = subprocess.run([HOOK], input=payload, capture_output=True, text=True, env=s["env"])
        assert r.returncode == 0, (payload, r.stderr)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_learn_capture: {len(tests)} passed")
