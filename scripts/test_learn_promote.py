#!/usr/bin/env python3
"""Tests for plugins/core/scripts/learn-promote.py. Run: python3 scripts/test_learn_promote.py"""
import datetime
import glob
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMOTE = os.path.join(ROOT, "plugins", "core", "scripts", "learn-promote.py")
EVIDENCE = "user: Stop piping test output through tail, read the real exit code."
TODAY = datetime.date.today()


def home():
    return tempfile.mkdtemp(prefix="learn-home-")


def repo(home_dir, digest=EVIDENCE):
    path = tempfile.mkdtemp(prefix="learn-promote-")
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    state = os.path.join(path, ".git", "claude-learn")
    os.makedirs(os.path.join(state, "digests"))
    write(os.path.join(state, "digests", "sess-1.txt"), "assistant: [tool: Bash]\n" + digest + "\n")
    return {"path": path, "home": home_dir, "queue": os.path.join(state, "queue"),
            "solutions": os.path.join(path, ".claude", "docs", "solutions")}


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def read(path):
    with open(path) as f:
        return f.read()


def proposal(**over):
    p = {"slug": "piped-exit-codes", "title": "Never judge tests through a pipe",
         "body": "Run the test command unpiped.\nA pipe reports the exit code of its last command.",
         "level": "project", "confidence": "med", "evidence": EVIDENCE}
    p.update(over)
    return {k: v for k, v in p.items() if v is not None}


def queue(r, p, name="p1.json"):
    write(os.path.join(r["queue"], name), p if isinstance(p, str) else json.dumps(p))


def run(r, *args, stdin="", env=None):
    e = {k: v for k, v in os.environ.items() if not k.startswith("HARNESS_LEARN")}
    e.update({"HOME": r["home"], **(env or {})})
    res = subprocess.run(["python3", PROMOTE, *args], cwd=r["path"], input=stdin, capture_output=True,
                         text=True, env=e)
    assert res.returncode == 0, res.stderr
    return res


def rejected(r):
    return [json.loads(read(f)) for f in glob.glob(os.path.join(r["queue"], "rejected", "*.json"))]


def frontmatter(path):
    head = read(path).split("---")[1]
    return dict(line.split(": ", 1) for line in head.strip().splitlines())


def test_valid_proposal_lands_with_frontmatter_and_index_line():
    r = repo(home())
    queue(r, proposal())
    run(r, "--now")
    fm = frontmatter(os.path.join(r["solutions"], "piped-exit-codes.md"))
    assert fm["confidence"] == "med" and fm["ttl_days"] == "90" and fm["seen"] == "1"
    assert fm["last_used"] == TODAY.isoformat()
    assert EVIDENCE in read(os.path.join(r["solutions"], "piped-exit-codes.md"))
    assert "[piped-exit-codes](piped-exit-codes.md)" in read(os.path.join(r["solutions"], "INDEX.md"))
    assert os.listdir(r["queue"]) == []


def test_each_reject_reason():
    cases = [
        (proposal(confidence="sure"), "schema"),
        (proposal(slug=None), "schema"),
        ("{not json", "schema"),
        (proposal(body="Rotate sk-" + "Z" * 24 + " now."), "secret"),
        (proposal(level="global", body="Edit /Users/me/project/app.ts first."), "absolute path"),
        (proposal(body="\n".join(f"line {i}" for i in range(16))), "15 lines"),
        (proposal(evidence="user: something nobody ever said in this session"), "evidence"),
    ]
    for p, reason in cases:
        r = repo(home())
        queue(r, p)
        run(r, "--now")
        got = rejected(r)
        assert len(got) == 1 and reason in got[0]["reject_reason"], (reason, got)
        assert not os.path.exists(os.path.join(r["solutions"], "piped-exit-codes.md")), reason


def test_project_lesson_may_name_absolute_paths():
    r = repo(home())
    queue(r, proposal(body="Edit /Users/me/project/app.ts first."))
    run(r, "--now")
    assert rejected(r) == []


def test_duplicate_of_index_line_is_rejected_and_bumps_seen():
    r = repo(home())
    queue(r, proposal())
    run(r, "--now")
    queue(r, proposal(), "p2.json")
    run(r, "--now")
    got = rejected(r)
    assert len(got) == 1 and "duplicate" in got[0]["reject_reason"]
    assert frontmatter(os.path.join(r["solutions"], "piped-exit-codes.md"))["seen"] == "2"
    queue(r, proposal(slug="other-slug", title="never judge tests through a pipe."), "p3.json")
    run(r, "--now")
    assert len(rejected(r)) == 2  # same title under another slug is still a duplicate


def test_past_ttl_and_unused_is_archived_never_deleted():
    r = repo(home())
    old = (TODAY - datetime.timedelta(days=91)).isoformat()
    for slug, last in (("stale-one", old), ("fresh-one", TODAY.isoformat())):
        write(os.path.join(r["solutions"], f"{slug}.md"),
              f"---\ntitle: {slug}\nconfidence: low\nttl_days: 90\nseen: 1\nlast_used: {last}\n---\n\n# {slug}\n")
    write(os.path.join(r["solutions"], "hand-written.md"), "---\ntitle: kept\n---\n\n# kept\n")
    write(os.path.join(r["solutions"], "INDEX.md"),
          "# Solutions Index\n\n- [stale-one](stale-one.md) — stale\n- [fresh-one](fresh-one.md) — fresh\n")
    run(r, "--now")
    assert os.path.exists(os.path.join(r["solutions"], "archive", "stale-one.md"))
    assert not os.path.exists(os.path.join(r["solutions"], "stale-one.md"))
    assert os.path.exists(os.path.join(r["solutions"], "fresh-one.md"))
    assert os.path.exists(os.path.join(r["solutions"], "hand-written.md"))
    index = read(os.path.join(r["solutions"], "INDEX.md"))
    assert "stale-one" not in index and "fresh-one" in index


def test_reading_a_lesson_marks_it_used():
    r = repo(home())
    path = os.path.join(r["solutions"], "stale-one.md")
    write(path, "---\ntitle: x\nconfidence: low\nttl_days: 90\nseen: 1\nlast_used: 2020-01-01\n---\n\n# x\n")
    run(r, "--touch", path)
    assert frontmatter(path)["last_used"] == TODAY.isoformat()


def test_same_global_slug_in_two_repos_is_promoted():
    h = home()
    first, second = repo(h), repo(h)
    global_file = os.path.join(h, ".claude", "docs", "solutions", "piped-exit-codes.md")
    queue(first, proposal(level="global"))
    run(first, "--now")
    assert not os.path.exists(global_file)
    queue(second, proposal(level="global"))
    run(second, "--now")
    assert frontmatter(global_file)["seen"] == "2"
    assert "[piped-exit-codes](piped-exit-codes.md)" in read(os.path.join(os.path.dirname(global_file), "INDEX.md"))


def test_project_lesson_is_never_promoted():
    h = home()
    for r in (repo(h), repo(h)):
        queue(r, proposal())
        run(r, "--now")
    assert not os.path.exists(os.path.join(h, ".claude", "docs", "solutions", "piped-exit-codes.md"))


def test_session_start_hook_mode_and_child_guard():
    r = repo(home())
    queue(r, proposal())
    out = run(r, stdin=json.dumps({"cwd": r["path"]}), env={"HARNESS_LEARN_CHILD": "1"})
    assert out.stdout == "" and os.listdir(r["queue"]) == ["p1.json"]
    out = run(r, stdin=json.dumps({"cwd": r["path"]}))
    assert "1 added" in json.loads(out.stdout)["systemMessage"]
    assert run(r, stdin="garbage").stdout == ""


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_learn_promote: {len(tests)} passed")
