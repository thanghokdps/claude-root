#!/usr/bin/env python3
"""learn-promote.py — land the lessons learn-capture.sh queued, retire stale ones, promote recurring ones. No LLM.

Drain: each <git-common-dir>/claude-learn/queue/*.json is validated (schema, no secret left, no absolute path
in a global lesson, body <= 15 lines, evidence quoted from a saved digest, not a duplicate of an INDEX line).
Folders: <H> = ${XDG_DATA_HOME:-~/.local/share}/claude-harness, outside every repo and outside ~/.claude (Claude Code
refuses Write/Edit there). <S> = <H>/repos/<repo>-<sha8>, this person's state for the repo (hooks/lib/state-dir.sh
computes the same path): <S>/specs/ (handoff, plans) and <S>/solutions/.
A project-level pass becomes .claude/solutions/<slug>.md (confidence, ttl_days: 90, seen: 1, last_used) plus an
INDEX line, committed for the team; a personal-level pass lands the same way in <S>/solutions/; a global-level pass
is only recorded for Promote, never written into the repo. A failure
moves to queue/rejected/ with reject_reason. A duplicate also counts as a recurrence: the existing lesson gets
seen + 1 and last_used today.
Retire: an auto-captured lesson (it has ttl_days) whose last_used is older than ttl_days moves to archive/
and leaves the INDEX. Never deleted. Applies to the project, personal and global solutions folders.
Promote: a global-level slug seen in >= 2 repos (<H>/global/repos.json) is copied to <H>/global/solutions/ with seen: N.
Migrate: what older kits kept in ~/.claude/docs/solutions, ~/.claude/claude-learn/ and an untracked <repo>/specs/
moves to <H> once, and so does an untracked .claude/docs/solutions/ (never shared, so personal). Nothing is
overwritten; a tracked .claude/docs/solutions/ is only reported, for a `git mv`.

Usage: SessionStart hook (event JSON on stdin; adds <S> to the session context, prints a systemMessage when
something changed) · --now (drain the current repo now and print a report; /compound runs it) ·
--touch <lesson.md> (mark used) · --state-dir (print <S>).
HARNESS_LEARN=0 or HARNESS_LEARN_CHILD set: the hook mode does nothing. Never exits non-zero.
"""
import datetime
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PATTERNS = os.path.join(HERE, "..", "hooks", "secret-patterns.txt")
KEYS = {"slug", "title", "body", "level", "confidence", "evidence"}
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ABS_PATH = re.compile(r"(?:/Users/|/home/|/root/|/private/|/var/folders/)\S+|\b[A-Za-z]:\\\S+")
INDEX_LINK = re.compile(r"^- \[([^\]]+)\]\(([^)]+)\)(.*)$")
SECTION = "## Auto-captured"
MAX_LINES, TTL_DAYS, MIN_EVIDENCE = 15, 90, 20
TODAY = datetime.date.today().isoformat()


def git(cwd, *args):
    r = subprocess.run(["git", "-C", cwd, "rev-parse", "--path-format=absolute", *args],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def secret_patterns():
    return [re.compile(p) for p in read(PATTERNS).splitlines() if p and not p.startswith("#")]


def squash(text):
    return " ".join(text.split()).lower()


def split_frontmatter(text):
    """(ordered key/value pairs, rest) for a flat `key: value` frontmatter; ([], text) when there is none."""
    m = re.match(r"\A---\n(.*?)\n---\n?", text, re.S)
    if not m:
        return [], text
    pairs = [tuple(part.strip() for part in line.split(":", 1)) for line in m.group(1).splitlines() if ":" in line]
    return pairs, text[m.end():]


def join_frontmatter(pairs, rest):
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in pairs) + "---\n" + rest


def set_fields(path, **fields):
    """Update frontmatter fields in place; returns False for a file that is not auto-captured (no ttl_days)."""
    pairs, rest = split_frontmatter(read(path))
    if "ttl_days" not in dict(pairs):
        return False
    pairs = [(k, str(fields.pop(k)) if k in fields else v) for k, v in pairs]
    write(path, join_frontmatter(pairs + [(k, str(v)) for k, v in fields.items()], rest))
    return True


def bump(path):
    seen = dict(split_frontmatter(read(path))[0]).get("seen", "1")
    set_fields(path, seen=int(seen) + 1 if seen.isdigit() else 2, last_used=TODAY)


def index_entries(index_path):
    """(slug, linked file or None, summary) per INDEX line."""
    folder = os.path.realpath(os.path.dirname(index_path))
    out = []
    for line in read(index_path).splitlines():
        m = INDEX_LINK.match(line)
        if m:
            summary = m.group(3).strip(" —-").split(" — ")[0]
            linked = os.path.join(folder, m.group(2))
            # The INDEX is repo content: only a plain file directly in its folder may be bumped, never ../ or a symlink.
            if os.path.islink(linked) or os.path.dirname(os.path.realpath(linked)) != folder:
                linked = None
            out.append((m.group(1), linked, summary))
    return out


def add_index_line(index_path, slug, title, confidence):
    line = f"- [{slug}]({slug}.md) — {title} — `{confidence}`"
    lines = read(index_path).splitlines() or ["# Solutions Index", ""]
    if SECTION not in lines:
        lines += ["", SECTION, ""] if lines[-1] else [SECTION, ""]
    at = lines.index(SECTION) + 1
    while at < len(lines) and not lines[at].startswith("## "):
        at += 1
    while lines[at - 1] == "":
        at -= 1
    lines.insert(at, line)
    write(index_path, "\n".join(lines) + "\n")


def drop_index_line(index_path, name):
    text = read(index_path)
    kept = [l for l in text.splitlines() if not (INDEX_LINK.match(l) and f"]({name})" in l)]
    if text and len(kept) != len(text.splitlines()):
        write(index_path, "\n".join(kept) + "\n")


def check(p, digests, indexes, patterns):
    """Reject reason, or None for a lesson that may land."""
    if not isinstance(p, dict) or set(p) != KEYS or not all(isinstance(p[k], str) and p[k].strip() for k in KEYS):
        return f"schema: needs exactly the string keys {', '.join(sorted(KEYS))}"
    if not SLUG.match(p["slug"]) or not 2 <= len(p["slug"]) <= 64:
        return "schema: slug must be kebab-case, 2-64 characters"
    if "\n" in p["title"].strip():
        return "schema: title must be one line"
    if p["level"] not in ("project", "personal", "global"):
        return "schema: level must be project, personal or global"
    if p["confidence"] not in ("low", "med", "high"):
        return "schema: confidence must be low, med or high"
    fields = "\n".join(p[k] for k in ("slug", "title", "body", "evidence"))
    for pat in patterns:
        if pat.search(fields):
            return f"secret: matches {pat.pattern}"
    if p["level"] == "global" and ABS_PATH.search(fields):
        return f"absolute path in a global lesson: {ABS_PATH.search(fields).group()}"
    lines = len(p["body"].strip().splitlines())
    if lines > MAX_LINES:
        return f"body is {lines} lines, over the {MAX_LINES} lines allowed"
    quote = squash(p["evidence"])
    if len(quote) < MIN_EVIDENCE or not any(quote in d for d in digests):
        return f"evidence: not a verbatim quote of {MIN_EVIDENCE}+ characters from a saved digest"
    for index_path in indexes:
        for slug, linked, summary in index_entries(index_path):
            if slug == p["slug"] or squash(summary).rstrip(".") == squash(p["title"]).rstrip("."):
                if linked:
                    bump(linked)
                return f"duplicate of INDEX line [{slug}] in {index_path}"
    return None


def lesson_text(p, seen=1):
    pairs = [("title", json.dumps(p["title"])), ("level", p["level"]), ("confidence", p["confidence"]),
             ("ttl_days", TTL_DAYS), ("seen", seen), ("last_used", TODAY), ("source", "learn-capture")]
    rest = f"\n# {p['title']}\n\n{p['body'].strip()}\n\nEvidence: \"{p['evidence'].strip()}\"\n"
    return join_frontmatter(pairs, rest)


def harness_home():
    data = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(data, "claude-harness")


def repo_state_dir(common):
    """<S>: keyed by the repo's resolved git common dir, so every worktree shares it."""
    real = os.path.realpath(common)
    name = os.path.basename(os.path.dirname(real)) + "-" + hashlib.sha1(real.encode()).hexdigest()[:8]
    return os.path.join(harness_home(), "repos", name)


def promote(p, repo_id, home_solutions):
    """Record the repo for a global slug; copy it to the global folder once >= 2 repos have it."""
    registry_path = os.path.join(harness_home(), "global", "repos.json")
    try:
        registry = json.loads(read(registry_path) or "{}")
    except ValueError:
        registry = {}
    repos = registry.setdefault(p["slug"], [])
    if repo_id not in repos:
        repos.append(repo_id)
    write(registry_path, json.dumps(registry, indent=1, sort_keys=True) + "\n")
    if len(repos) < 2:
        return False
    target = os.path.join(home_solutions, p["slug"] + ".md")
    if os.path.exists(target):
        set_fields(target, seen=len(repos), last_used=TODAY)
    else:
        write(target, lesson_text(p, seen=len(repos)))
    index = os.path.join(home_solutions, "INDEX.md")
    if p["slug"] not in [e[0] for e in index_entries(index)]:
        add_index_line(index, p["slug"], p["title"], p["confidence"])
    return True


def move_missing(src, dst, counts):
    """Move src to dst, entry by entry, where dst has nothing yet; an empty source folder is then removed."""
    if not os.path.lexists(src):
        return
    if not os.path.lexists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        counts["migrated"] += 1
    elif os.path.isdir(src) and not os.path.islink(src) and os.path.isdir(dst):
        for name in sorted(os.listdir(src)):
            move_missing(os.path.join(src, name), os.path.join(dst, name), counts)
        try:
            os.rmdir(src)
        except OSError:
            pass  # something stayed because dst already had it: left in place, never overwritten


def tracked(top, rel):
    r = subprocess.run(["git", "-C", top, "ls-files", "--", rel], capture_output=True, text=True)
    return r.returncode != 0 or bool(r.stdout.strip())


def migrate(top, state_dir, counts):
    """Older kits: global lessons in ~/.claude/docs/solutions, state in ~/.claude/claude-learn, specs/ in the repo."""
    old = os.path.join(os.path.expanduser("~"), ".claude")
    home = harness_home()
    move_missing(os.path.join(old, "docs", "solutions"), os.path.join(home, "global", "solutions"), counts)
    move_missing(os.path.join(old, "claude-learn", "repos.json"), os.path.join(home, "global", "repos.json"), counts)
    move_missing(os.path.join(old, "claude-learn", "solutions", os.path.basename(state_dir)),
                 os.path.join(state_dir, "solutions"), counts)
    if not tracked(top, "specs"):
        move_missing(os.path.join(top, "specs"), os.path.join(state_dir, "specs"), counts)
    old_team = os.path.join(".claude", "docs", "solutions")
    if not tracked(top, old_team):  # never committed, so nobody else had it: personal
        move_missing(os.path.join(top, old_team), os.path.join(state_dir, "solutions"), counts)
    elif os.path.isdir(os.path.join(top, old_team)):
        return "team lessons moved to .claude/solutions/: run `git mv .claude/docs/solutions .claude/solutions`"
    return None


def drain(state, solutions, personal, home_solutions, repo_id, counts):
    queue = os.path.join(state, "queue")
    digests = [squash(read(f)) for f in glob.glob(os.path.join(state, "digests", "*.txt"))]
    indexes = [os.path.join(d, "INDEX.md") for d in (solutions, personal, home_solutions)]
    patterns = secret_patterns()
    for path in sorted(glob.glob(os.path.join(queue, "*.json"))):
        claimed = os.path.join(queue, f".{os.path.basename(path)}.{os.getpid()}")
        try:
            os.rename(path, claimed)  # another session draining at the same moment loses the race, not the file
        except OSError:
            continue
        raw = read(claimed)
        try:
            p = json.loads(raw)
        except ValueError:
            p = None
        reason = check(p, digests, indexes, patterns) if p is not None else "schema: not valid JSON"
        if reason:
            record = dict(p) if isinstance(p, dict) else {"raw": raw}
            record["reject_reason"] = reason
            write(os.path.join(queue, "rejected", os.path.basename(path)), json.dumps(record, indent=1) + "\n")
            counts["rejected"] += 1
        elif p["level"] == "global":
            # Only repos.json remembers it until a second repo sees it: a team repo never carries kit lessons.
            counts["promoted" if promote(p, repo_id, home_solutions) else "staged"] += 1
        else:
            folder = personal if p["level"] == "personal" else solutions
            write(os.path.join(folder, p["slug"] + ".md"), lesson_text(p))
            add_index_line(os.path.join(folder, "INDEX.md"), p["slug"], p["title"], p["confidence"])
            counts["added"] += 1
        os.remove(claimed)


def retire(solutions, counts):
    today = datetime.date.today()
    for path in sorted(glob.glob(os.path.join(solutions, "*.md"))):
        fm = dict(split_frontmatter(read(path))[0])
        try:
            last = datetime.date.fromisoformat(fm["last_used"])
            ttl = int(fm["ttl_days"])
        except (KeyError, ValueError):
            continue  # hand-written (/compound) lessons have no TTL and never retire
        if (today - last).days <= ttl:
            continue
        name = os.path.basename(path)
        target = os.path.join(solutions, "archive", name)
        if os.path.exists(target):
            target = target[:-3] + f"-{today.isoformat()}.md"
        os.makedirs(os.path.dirname(target), exist_ok=True)
        os.replace(path, target)
        drop_index_line(os.path.join(solutions, "INDEX.md"), name)
        counts["archived"] += 1


def run(cwd):
    """(counts, rejected dir, <S>, folders, hint); <S> is None outside a repo."""
    top, common = git(cwd, "--show-toplevel"), git(cwd, "--git-common-dir")
    counts = {"added": 0, "staged": 0, "rejected": 0, "archived": 0, "promoted": 0, "migrated": 0}
    if not top or not common:
        return counts, None, None, None, None
    state = os.path.join(common, "claude-learn")
    state_dir = repo_state_dir(common)
    hint = migrate(top, state_dir, counts)
    folders = (os.path.join(top, ".claude", "solutions"), os.path.join(state_dir, "solutions"),
               os.path.join(harness_home(), "global", "solutions"))
    if os.path.isdir(os.path.join(state, "queue")):
        drain(state, *folders, os.path.realpath(common), counts)
    for folder in folders:
        retire(folder, counts)
    return counts, os.path.join(state, "queue", "rejected"), state_dir, folders, hint


def report(counts):
    return ", ".join(f"{n} {k}" for k, n in counts.items())


def main(argv):
    if argv[:1] == ["--touch"] and len(argv) == 2:
        set_fields(argv[1], last_used=TODAY)
    elif argv[:1] == ["--state-dir"]:
        common = git(os.getcwd(), "--git-common-dir")
        if common:
            print(repo_state_dir(common))
    elif argv[:1] == ["--now"]:
        counts, rejected, _, _, hint = run(os.getcwd())
        print(f"learn-promote: {report(counts)}" + (f" (rejects in {rejected})" if counts["rejected"] else "")
              + (f"; {hint}" if hint else ""))
    elif not argv:
        if os.environ.get("HARNESS_LEARN") == "0" or os.environ.get("HARNESS_LEARN_CHILD"):
            return
        try:
            ev = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            return
        counts, rejected, state_dir, folders, hint = run(
            ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        if not state_dir:
            return
        out = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": (
            f"Personal Claude state for this repo: {state_dir}. In every skill, rule and hook, specs/ means "
            f"{state_dir}/specs/ (HANDOFF.md, <slug>/PLAN.md, audit/): never create specs/ in the repo. "
            f"Lessons: team {folders[0]}/ (committed), personal {folders[1]}/, global {folders[2]}/.")}}
        notes = ([f"Learnings: {report(counts)}."] if any(counts.values()) else []) + \
                ([f"Rejects: {rejected}"] if counts["rejected"] else []) + ([hint] if hint else [])
        if notes:
            out["systemMessage"] = " ".join(notes)
        print(json.dumps(out))


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as e:  # a hook never fails the session; the reason goes to stderr
        print(f"learn-promote: {e}", file=sys.stderr)
    sys.exit(0)
