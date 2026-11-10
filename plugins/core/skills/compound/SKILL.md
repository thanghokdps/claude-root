---
model: opus
effort: high
name: compound
description: Crystallize learnings from the current session into persistent solutions/ lesson files (team, personal or global). Run at the end of any session with significant work — mistakes found, solutions discovered, patterns identified. Prevents agents from repeating the same mistakes across sessions.
when_to_use: end of a session with a tricky fix or a mistake that cost time, "save this learning", "lưu bài học", "ghi lại để lần sau không lặp lại", after /retro, a commit hook reminds that many files changed
---

# Compound — Crystallize Session Learnings

Extract what was learned in this session and write it to a `solutions/` folder (Step 3) so future agents start with this knowledge already loaded.

**Run when:**

- A session involved a significant bug fix or tricky problem
- An agent made a mistake that cost time
- A better pattern or approach was discovered
- A discussion produced a clear best-practice decision
- ≥ 5 files were changed in a session (commit hook will remind you)

It also drains the lessons the background reflector queued: run `python3 -I "${CLAUDE_PLUGIN_ROOT}"/scripts/learn-promote.py --now` first and skip any learning it just added.

---

## Step 1 — Review the session

Scan the current conversation for:

| Signal                             | What to capture                                |
| ---------------------------------- | ---------------------------------------------- |
| Agent made a wrong assumption      | → lesson: "always check X before assuming Y"   |
| Mistake repeated > once            | → critical pattern: "never do Z"               |
| Approach that worked well          | → solution: "use A instead of B for this case" |
| Architectural decision made        | → decision: "we chose X because Y"             |
| Surprising constraint discovered   | → constraint: "X doesn't work when Y"          |
| Discussion that ended in consensus | → pattern: "agreed approach is X"              |

Ignore: routine implementation details, boilerplate, things already in docs.

---

## Step 2 — Classify each learning

Assign each learning:

- **Scope**: `global` (applies to any project), `project` (this codebase, and the whole team needs it) or `personal` (this codebase, only this user needs it: their machine, paths, local setup). Unsure between `project` and `personal` → `personal`
- **Category**: one of:
  - `mistakes` — things agents got wrong
  - `patterns` — approaches that worked well
  - `decisions` — architectural/design choices made
  - `constraints` — non-obvious limitations discovered
  - `solutions` — specific solutions to recurring problems
- **Severity**: `critical` (read before every task) | `normal` (read when relevant)

---

## Step 3 — Write solution files

The session start context names all three folders; `python3 -I ${CLAUDE_PLUGIN_ROOT}/scripts/learn-promote.py --state-dir` prints this repo's state dir `<S>`.

**For global learnings** → write to `~/.local/share/claude-harness/global/solutions/<slug>.md`
**For project learnings** → write to `.claude/solutions/<slug>.md` and commit it with the work
**For personal learnings** → write to `<S>/solutions/<slug>.md` (outside the repo, never committed)

Flat, no category folders: `learn-promote.py` dedupes, bumps and retires only `*.md` directly in the folder.

Each file format:

```markdown
---
title: <short title>
category: <mistakes|patterns|decisions|constraints|solutions>
severity: <critical|normal>
tags: [<tag1>, <tag2>]
confirmed_at: <YYYY-MM-DD>
applies_to: <global|project-name>
---

# <title>

## Problem / Context

<What situation triggers this? What went wrong or what was unclear?>

## Solution / Rule

<The correct approach — specific and actionable>

## Why

<Why this rule exists — the reasoning or incident that caused it>

## Example

<Before/after code snippet or concrete example — optional but preferred>

## Related

- <link to other solution slug if connected>
```

---

## Step 4 — Update INDEX.md

**Global**: update `~/.local/share/claude-harness/global/solutions/INDEX.md`
**Project**: update `.claude/solutions/INDEX.md`
**Personal**: update `<S>/solutions/INDEX.md`

Format (links are flat: the category is a heading, never a folder):

```markdown
# Solutions Index

> Entries older than 30 days with no `reconfirmed_at` should be reviewed for staleness.

## Critical patterns (read before every task)

- [slug](slug.md) — one-line summary — `confirmed_at`

## By category

### mistakes

- [slug](slug.md) — one-line summary

### patterns

- [slug](slug.md) — one-line summary

### decisions

- [slug](slug.md) — one-line summary

### constraints

- [slug](slug.md) — one-line summary

### solutions

- [slug](slug.md) — one-line summary
```

---

## Step 5 — Report

```
Compound complete.

Learnings crystallized: N
  critical: <slugs>
  normal:   <slugs>

Written to:
  global:   ~/.local/share/claude-harness/global/solutions/
  project:  .claude/solutions/ (commit it)
  personal: <S>/solutions/

Next session: agents will load these automatically via each folder's INDEX.md
```

---

## Rules

- Only capture what is **surprising or non-obvious** — don't write down things already in docs
- Be **specific**: "never call X without Y" beats "be careful with X"
- One learning per file — no multi-topic blobs
- Mark as `critical` only if a future agent would likely make the same mistake without this
- Entries older than 30 days without `reconfirmed_at` are stale — update or delete
