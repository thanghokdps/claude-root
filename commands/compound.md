---
description: Crystallize session learnings into .claude/docs/solutions/ — mistakes made, patterns discovered, decisions reached. Run after any session with significant debugging or design work.
argument-hint: "[optional: specific topic to crystallize]"
---

# Compound

Extract non-obvious learnings from this session and write them to `.claude/docs/solutions/` so future agents don't repeat the same mistakes.

**Run when:**
- An agent made a wrong assumption that cost time
- A tricky bug was solved in a non-obvious way
- A design decision was reached through discussion
- A surprising constraint was discovered
- ≥ 5 files were changed this session

## Step 1 — Review the session

Scan the conversation for:

| Signal | What to capture |
|--------|----------------|
| Wrong assumption by agent | "always check X before assuming Y" |
| Bug with non-obvious root cause | "Z fails when Y because..." |
| Better approach found | "use A not B for this case" |
| Architectural decision made | "we chose X because Y" |
| Surprising constraint | "X doesn't work when Y" |

Ignore routine implementation — only capture what is **surprising or non-obvious**.

## Step 2 — Classify each learning

- **Scope**: `project` (this project specific) or `global` (any project)
- **Category**: `mistakes` | `patterns` | `decisions` | `constraints` | `solutions`
- **Severity**: `critical` (future agent will repeat this) | `normal`

## Step 3 — Write solution files

For **project** learnings → `.claude/docs/solutions/<category>/<slug>.md`
For **global** learnings → `~/.claude/docs/solutions/<category>/<slug>.md`

```markdown
---
title: <short title>
category: <mistakes|patterns|decisions|constraints|solutions>
severity: <critical|normal>
tags: [...]
confirmed_at: <YYYY-MM-DD>
---

# <title>

## Problem / Context
<what situation triggers this>

## Solution / Rule
<correct approach — specific and actionable>

## Why
<reason this rule exists>

## Example
<before/after or concrete example>
```

## Step 4 — Update INDEX.md

Update `.claude/docs/solutions/INDEX.md`:
- Add to "Critical patterns" if `severity: critical`
- Add to the appropriate category section

## Step 5 — Report

```
Compound complete.

Learnings crystallized: N
  critical: <slugs>
  normal: <slugs>

Written to: .claude/docs/solutions/
```
