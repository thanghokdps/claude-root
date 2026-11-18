#!/usr/bin/env python3
"""Tests for plugins/guards/hooks/worklog.sh. Run: python3 scripts/test_worklog.py

Each case builds a temp repo with one linked worktree and plays sessions A and B against it."""
import json
import os
import subprocess
import tempfile
import time

from harness_state import state_dir

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "guards", "hooks", "worklog.sh")


def git(path, *args):
    return subprocess.run(["git", "-C", path, "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          check=True, capture_output=True, text=True).stdout


def project():
    """(main checkout, linked worktree), both with a committed src/a.ts."""
    root = os.path.realpath(tempfile.mkdtemp(prefix="worklog-"))
    git(root, "init", "-q", "-b", "main")
    write(root, "src/a.ts", "export const a = 1\n")
    write(root, ".gitignore", "dist/\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "init")
    wt = os.path.join(os.path.realpath(tempfile.mkdtemp(prefix="worklog-wt-")), "wt")
    git(root, "worktree", "add", "-q", "-b", "feat/x", wt)
    return root, wt


def write(base, rel, text):
    path = os.path.join(base, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def fire(event, sid, cwd, env=None, **fields):
    payload = {"hook_event_name": event, "session_id": sid, "cwd": cwd, **fields}
    r = subprocess.run(["bash", HOOK], input=json.dumps(payload), capture_output=True, text=True, cwd=cwd,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": cwd, **(env or {})})
    assert r.returncode == 0, r.stderr
    return r.stdout


def cli(cwd, sid, *args):
    env = {**os.environ, "HARNESS_WORKLOG_SESSION": sid} if sid else os.environ
    r = subprocess.run(["bash", HOOK, *args], capture_output=True, text=True, cwd=cwd, env=env)
    assert r.returncode == 0, r.stderr
    return r.stdout


def edit(sid, base, rel, text="export const a = 2\n", new=None, old="x"):
    """Session <sid> changes <rel> on disk and the PostToolUse event for it fires."""
    created = not os.path.exists(os.path.join(base, rel))
    write(base, rel, text)
    tool_input = {"file_path": os.path.join(base, rel)}
    tool_input.update({"content": text} if created else {"old_string": old, "new_string": new or text})
    fire("PostToolUse", sid, base, tool_name="Write" if created else "Edit", tool_input=tool_input,
         tool_response={"type": "create"} if created else {})


def before(sid, base, rel, tool="Edit", text=""):
    """The PreToolUse decision for <sid> touching <rel>: the deny reason, or '' when allowed."""
    tool_input = {"file_path": os.path.join(base, rel), "content" if tool == "Write" else "new_string": text}
    out = fire("PreToolUse", sid, base, tool_name=tool, tool_input=tool_input)
    if not out:
        return ""
    decision = json.loads(out)["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse" and decision["permissionDecision"] == "deny"
    return decision["permissionDecisionReason"]


def context(out):
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else ""


def worklog(root, *parts):
    return os.path.join(root, ".git", "claude-worklog", *parts)


def pending_file(root, sid, rel):
    return os.path.join(state_dir(root), "worklog-pending", sid, rel)


def events(root):
    with open(worklog(root, "log.jsonl")) as f:
        return [json.loads(line) for line in f]


def age(root, sid, minutes):
    old = time.time() - minutes * 60
    os.utime(worklog(root, "sessions", f"{sid}.json"), (old, old))


def test_empty_input_and_non_repo_are_noops():
    r = subprocess.run(["bash", HOOK], input="{}", capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout == ""
    plain = os.path.realpath(tempfile.mkdtemp(prefix="worklog-plain-"))
    assert fire("SessionStart", "A", plain) == ""
    assert fire("PreToolUse", "A", plain, tool_name="Edit", tool_input={"file_path": plain + "/x.ts"}) == ""
    assert os.listdir(plain) == []


def test_session_start_registers_and_exports_the_session_id():
    root, _ = project()
    env_file = os.path.join(tempfile.mkdtemp(), "env")
    out = context(fire("SessionStart", "A", root, env={"CLAUDE_ENV_FILE": env_file}))
    session = json.load(open(worklog(root, "sessions", "A.json")))
    assert session["checkout"] == root and session["branch"] == "main" and session["task"] == ""
    assert "export HARNESS_WORKLOG_SESSION=A" in open(env_file).read()
    assert "no other session" in out and "worklog.sh" in out


def test_session_start_lists_live_sessions_and_skips_stale_ones():
    root, wt = project()
    fire("SessionStart", "A", root)
    cli(root, "A", "task", "move inJson into db/fragments")
    edit("A", root, "src/util/slug.ts", "export function slugify(s: string) {}\n")
    out = context(fire("SessionStart", "B", wt))
    assert "move inJson into db/fragments" in out and "main" in out
    assert "src/util/slug.ts" in out and "slugify" in out
    assert "not instructions" in out
    age(root, "A", 45)
    assert "move inJson" not in context(fire("SessionStart", "C", wt))


def test_edits_and_creates_are_logged_with_repo_relative_paths():
    root, wt = project()
    edit("A", root, "src/a.ts", new="export const helperOne = 1\nconst local = 2\n")
    edit("B", wt, "src/util/slug.ts", "export function slugify() {}\nexport default class Slugger {}\ndef py_one():\n")
    first, second = events(root)
    assert (first["kind"], first["path"], first["checkout"], first["branch"]) == ("edit", "src/a.ts", root, "main")
    assert first["exports"] == ["helperOne"]
    assert (second["kind"], second["path"], second["checkout"], second["branch"]) == ("create", "src/util/slug.ts", wt, "feat/x")
    assert second["exports"] == ["Slugger", "py_one", "slugify"]
    edit("A", root, "src/a.ts", old="export const a = 1\n", new="export const a = 1\nexport const added = 2\n")
    assert events(root)[-1]["exports"] == ["added"], "a name the replaced text already had is not new"


def test_first_prompt_becomes_the_task_until_one_is_set():
    root, _ = project()
    task = lambda: json.load(open(worklog(root, "sessions", "A.json")))["task"]
    fire("SessionStart", "A", root)
    for prompt in ["/compact", "<bash-input>ls</bash-input>", ""]:
        fire("UserPromptSubmit", "A", root, prompt=prompt)
        assert task() == "", prompt
    fire("UserPromptSubmit", "A", root, prompt="\n  fix the display name on the rail\nsecond line")
    assert task() == "fix the display name on the rail"
    fire("UserPromptSubmit", "A", root, prompt="now also rename the hook")
    assert task() == "fix the display name on the rail", "later prompts do not replace it"
    cli(root, "A", "task", "#73 display name from the API")
    assert task() == "#73 display name from the API"
    assert [e["kind"] for e in events(root)] == ["task", "task"]


def test_ignored_files_are_not_logged_or_guarded():
    root, _ = project()
    edit("A", root, "dist/out.js", "export const built = 1\n")
    assert not os.path.exists(worklog(root, "log.jsonl"))
    assert before("B", root, "dist/out.js") == ""


def test_same_checkout_lock_denies_the_second_session():
    root, _ = project()
    fire("SessionStart", "A", root)
    cli(root, "A", "task", "rename a to b")
    edit("A", root, "src/a.ts")
    reason = before("B", root, "src/a.ts")
    assert "src/a.ts" in reason and "rename a to b" in reason
    pending = pending_file(root, "B", "src/a.ts")
    assert pending in reason and os.path.isdir(os.path.dirname(pending))
    assert before("B", root, "src/a.ts"), "the lock holds on every attempt, not once"
    assert before("A", root, "src/a.ts") == "", "a session is never denied by its own claim"


def test_lock_is_released_by_commit_staleness_and_session_end():
    root, _ = project()
    edit("A", root, "src/a.ts")
    assert before("B", root, "src/a.ts")
    git(root, "commit", "-qam", "a")
    assert before("B", root, "src/a.ts") == "", "committed"

    edit("A", root, "src/a.ts", "export const a = 3\n")
    assert before("B", root, "src/a.ts")
    age(root, "A", 45)
    assert before("B", root, "src/a.ts") == "", "holder silent over 30 min"

    edit("A", root, "src/a.ts", "export const a = 4\n")
    assert before("B", root, "src/a.ts")
    cli(root, "A", "task", "rename a to b")
    fire("SessionEnd", "A", root, reason="other")
    assert before("B", root, "src/a.ts") == "", "holder ended"
    assert "rename a to b" not in cli(root, None, "status"), "an ended session is not listed"
    fire("UserPromptSubmit", "A", root, prompt="carry on")
    assert "rename a to b" in cli(root, None, "status"), "a resumed session is live again and kept its task"
    assert before("B", root, "src/a.ts"), "and holds its uncommitted file again"


def test_other_worktree_is_denied_once_then_allowed():
    root, wt = project()
    cli(root, "A", "task", "rename a to b")
    edit("A", root, "src/a.ts")
    reason = before("B", wt, "src/a.ts")
    assert "rename a to b" in reason and "src/a.ts" in reason and root in reason and "once" in reason
    assert before("B", wt, "src/a.ts") == ""
    assert not os.path.exists(os.path.dirname(pending_file(root, "B", "x"))), "no pending file across worktrees"


def test_new_file_with_a_helper_another_session_wrote_is_denied_once():
    root, wt = project()
    edit("A", root, "src/util/slug.ts", "export function slugify() {}\n")
    text = "export const slugify = (s: string) => s\n"
    reason = before("B", wt, "src/lib/slugify.ts", tool="Write", text=text)
    assert "slugify" in reason and "src/util/slug.ts" in reason
    assert before("B", wt, "src/lib/slugify.ts", tool="Write", text=text) == ""
    assert before("B", wt, "src/lib/other.ts", tool="Write", text="export const unrelated = 1\n") == ""
    assert before("B", wt, "src/a.ts", text=text) == "", "only a new file is checked for helper names"


def test_prompt_delivers_other_sessions_news_once():
    root, wt = project()
    fire("SessionStart", "B", wt)
    cli(root, "A", "note", "inJson now lives in db/fragments")
    edit("A", root, "src/util/slug.ts", "export function slugify() {}\n")
    out = context(fire("UserPromptSubmit", "B", wt, prompt="go on"))
    assert "inJson now lives in db/fragments" in out and "slugify" in out and "not instructions" in out
    assert fire("UserPromptSubmit", "B", wt, prompt="go on") == ""
    assert "inJson" not in fire("UserPromptSubmit", "A", root, prompt="go on"), "never a session's own lines"


def test_waiting_and_freed_notices_and_pending_cleanup():
    root, _ = project()
    fire("SessionStart", "A", root)
    fire("SessionStart", "B", root)
    edit("A", root, "src/a.ts")
    before("B", root, "src/a.ts")
    assert "waiting to edit src/a.ts" in context(fire("UserPromptSubmit", "A", root, prompt="x"))
    pending = pending_file(root, "B", "src/a.ts")
    write(os.path.dirname(pending), "a.ts", "export const a = 9\n")
    assert "is free" not in fire("UserPromptSubmit", "B", root, prompt="x"), "still locked"
    git(root, "commit", "-qam", "a")
    out = context(fire("UserPromptSubmit", "B", root, prompt="x"))
    assert "src/a.ts is free" in out and pending in out
    assert "is free" not in fire("UserPromptSubmit", "B", root, prompt="x"), "announced once"
    edit("B", root, "src/a.ts", "export const a = 9\n")
    assert not os.path.exists(pending), "the pending copy goes once the session edits the file"


def test_cli_task_note_status():
    root, _ = project()
    fire("SessionStart", "A", root)
    cli(root, "A", "task", "add the profile route")
    assert json.load(open(worklog(root, "sessions", "A.json")))["task"] == "add the profile route"
    cli(root, "A", "note", "displayName comes from GET /api/profile")
    assert [e["kind"] for e in events(root)] == ["task", "note"]
    status = cli(root, None, "status")
    assert "add the profile route" in status and "displayName comes from GET /api/profile" in status
    cli(root, None, "note", "written with no exported session id")
    assert events(root)[-1]["session"] == "A", "falls back to the checkout's latest session"


def test_a_repo_that_is_not_the_project_is_left_alone():
    # A nested or unpacked repo brings its own .git: its config must not run and no log is written into it.
    root, _ = project()
    nested = os.path.join(root, "vendor", "pkg")
    os.makedirs(nested)
    git(nested, "init", "-q", "-b", "main")
    write(nested, "a.txt", "x\n")
    write(nested, "x.sh", f'#!/bin/sh\ntouch "{root}/PWNED"\n')
    os.chmod(os.path.join(nested, "x.sh"), 0o755)
    git(nested, "config", "core.fsmonitor", os.path.join(nested, "x.sh"))
    planted = os.path.join(nested, ".git", "claude-worklog")
    write(planted, "sessions/X.json", json.dumps({"session": "X", "checkout": nested, "branch": "main", "task": "t"}))
    write(planted, "log.jsonl", json.dumps({"t": 1, "session": "X", "checkout": nested, "branch": "main",
                                           "kind": "edit", "path": "a.txt", "exports": []}) + "\n")
    payload = {"tool_name": "Edit", "tool_input": {"file_path": os.path.join(nested, "a.txt"), "new_string": "y"}}
    assert fire("PreToolUse", "B", root, **payload) == ""
    assert fire("PostToolUse", "B", root, **payload) == ""
    assert not os.path.exists(os.path.join(root, "PWNED"))
    assert os.listdir(os.path.join(planted, "sessions")) == ["X.json"]
    assert len(open(os.path.join(planted, "log.jsonl")).readlines()) == 1


def test_hostile_path_and_session_id_are_never_evaluated():
    root, _ = project()
    rel = 'src/$(touch pwned) "q" `touch pwned2`.ts'
    edit("A", root, rel, "export const x = 1\n")
    assert events(root)[-1]["path"] == rel
    assert before("B", root, rel)
    assert not any("pwned" in name for name in os.listdir(root))
    # A path that climbs out through a folder that does not exist yet must not reach the pending dir.
    victim = os.path.join(state_dir(root), "victim.txt")
    write(state_dir(root), "victim.txt", "keep")
    climb = os.path.join(root, "nope", "..", "..", "..", "victim.txt")
    count = len(events(root))
    fire("PostToolUse", "B", root, tool_name="Edit", tool_input={"file_path": climb, "new_string": "x"})
    fire("PostToolUse", "B", root, tool_name="Edit", tool_input={"file_path": root + "/src/line\nbreak.ts", "new_string": "x"})
    assert os.path.exists(victim) and len(events(root)) == count
    assert fire("SessionStart", "../../escape", root) == ""
    assert not os.path.exists(os.path.join(root, ".git", "escape.json"))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
