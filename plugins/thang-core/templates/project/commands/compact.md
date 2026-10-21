---
description: Compact the current conversation — summarize what's done, write HANDOFF.md so tomorrow's session resumes with full context. Run when context is getting long or before ending a session.
argument-hint: "[optional: focus area to summarize]"
---

# Compact

Summarize this session and write persistent state so the next session picks up without re-explaining.

**Note:** Claude Code auto-compacts within a session. This command handles cross-session persistence.

## Step 1 — Summarize

Write a concise summary of this session:

```
What was done:
- <bullet: specific file:line or commit sha>

Key decisions made:
- <bullet: decisions future agents need to know>

Discoveries (non-obvious constraints or surprises):
- <bullet>

Current state:
- Branch: <branch>
- Staged: <files or "none">
- WIP (unstaged): <files or "none">

Next steps:
- <concrete, specific — a fresh agent can continue from here>

Open questions:
- <anything needing human input>
```

## Step 2 — Write specs/HANDOFF.md

Save the summary above to `specs/HANDOFF.md` (overwrite — only latest matters).

```bash
mkdir -p specs
```

Format:
```markdown
# Handoff — <YYYY-MM-DD HH:MM>

## What was done
<bullets>

## Key decisions
<bullets>

## Discoveries
<bullets>

## Current state
Branch: <branch>
Staged: <files or none>
WIP: <files or none>

## Next steps
<concrete bullets>

## Open questions
<bullets or none>

## Context to reload
- .claude/docs/index.md
- .claude/docs/solutions/INDEX.md
- ~/.claude/docs/solutions/INDEX.md
```

## Step 3 — Merge learnings into solutions

For each item in "Key decisions" and "Discoveries":
- Is it surprising or non-obvious? Would another agent repeat this mistake?
- If yes → write to `.claude/docs/solutions/<category>/<slug>.md` + update INDEX.md
- If no → leave in HANDOFF.md only

## Step 4 — Report

```
Compact complete.

Written: specs/HANDOFF.md
Solutions updated: <N files or "none">

Next session: CLAUDE.md will auto-load HANDOFF.md — no need to re-explain anything.
```
