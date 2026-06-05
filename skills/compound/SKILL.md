---
model: sonnet
effort: high
name: compound
description: Crystallize learnings from the current session into persistent docs/solutions/ files. Run at the end of any session with significant work — mistakes found, solutions discovered, patterns identified. Prevents agents from repeating the same mistakes across sessions.
---

# Compound — Crystallize Session Learnings

Extract what was learned in this session and write it to `docs/solutions/` so future agents start with this knowledge already loaded.

**Run when:**
- A session involved a significant bug fix or tricky problem
- An agent made a mistake that cost time
- A better pattern or approach was discovered
- A discussion produced a clear best-practice decision
- ≥ 5 files were changed in a session (commit hook will remind you)

---

## Step 1 — Review the session

Scan the current conversation for:

| Signal | What to capture |
|--------|----------------|
| Agent made a wrong assumption | → lesson: "always check X before assuming Y" |
| Mistake repeated > once | → critical pattern: "never do Z" |
| Approach that worked well | → solution: "use A instead of B for this case" |
| Architectural decision made | → decision: "we chose X because Y" |
| Surprising constraint discovered | → constraint: "X doesn't work when Y" |
| Discussion that ended in consensus | → pattern: "agreed approach is X" |

Ignore: routine implementation details, boilerplate, things already in docs.

---

## Step 2 — Classify each learning

Assign each learning:

- **Scope**: `global` (applies to any project) or `project` (specific to this codebase)
- **Category**: one of:
  - `mistakes` — things agents got wrong
  - `patterns` — approaches that worked well
  - `decisions` — architectural/design choices made
  - `constraints` — non-obvious limitations discovered
  - `solutions` — specific solutions to recurring problems
- **Severity**: `critical` (read before every task) | `normal` (read when relevant)

---

## Step 3 — Write solution files

**For global learnings** → write to `~/.claude/docs/solutions/<category>/<slug>.md`
**For project learnings** → write to `.claude/docs/solutions/<category>/<slug>.md`

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

**Global**: update `~/.claude/docs/solutions/INDEX.md`
**Project**: update `.claude/docs/solutions/INDEX.md`

Format:

```markdown
# Solutions Index

> Entries older than 30 days with no `reconfirmed_at` should be reviewed for staleness.

## Critical patterns (read before every task)

- [slug](category/slug.md) — one-line summary — `confirmed_at`

## By category

### mistakes
- [slug](mistakes/slug.md) — one-line summary

### patterns
- [slug](patterns/slug.md) — one-line summary

### decisions
- [slug](decisions/slug.md) — one-line summary

### constraints
- [slug](constraints/slug.md) — one-line summary

### solutions
- [slug](solutions/slug.md) — one-line summary
```

---

## Step 5 — Write session breadcrumb

Append to `specs/STATE.md` (create if missing):

```markdown
## Session — <YYYY-MM-DD HH:MM>

**Work done:** <1–2 sentences>
**Commits:** <sha list>
**Learnings crystallized:** <slugs written to solutions/>
**Open items:** <anything unfinished or unresolved>
**Resume from:** <what to read first in the next session>
```

---

## Step 6 — Report

```
Compound complete.

Learnings crystallized: N
  critical: <slugs>
  normal:   <slugs>

Written to:
  global:  ~/.claude/docs/solutions/
  project: .claude/docs/solutions/

Session breadcrumb: specs/STATE.md

Next session: agents will load these automatically via docs/solutions/INDEX.md
```

---

## Rules

- Only capture what is **surprising or non-obvious** — don't write down things already in docs
- Be **specific**: "never call X without Y" beats "be careful with X"
- One learning per file — no multi-topic blobs
- Mark as `critical` only if a future agent would likely make the same mistake without this
- Entries older than 30 days without `reconfirmed_at` are stale — update or delete
