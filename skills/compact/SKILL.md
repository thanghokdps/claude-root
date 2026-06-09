---
model: sonnet
effort: high
name: compact
description: Compact the current conversation — summarize what's been done, merge into persistent memory and HANDOFF.md, so the next session resumes with full context. Run when conversation is getting long or before ending a session.
---

# Compact

Summarize the current session, merge into persistent files, prepare for next session.

**Claude Code already auto-compacts within a session.** This skill handles the cross-session case — writing state to disk so tomorrow's session starts with full context.

---

## When to run

- Conversation is getting long (context budget < 40%)
- About to end a session with unfinished work
- Switching context (different feature, different agent)
- After a long debug session — before the next task

---

## Step 0 — Run headroom learn (if installed)

If `headroom` is available, mine this session's failures before writing HANDOFF:

```bash
command -v headroom >/dev/null && headroom learn
```

This extracts corrections from failed tool calls and writes them to headroom's local model — complementing the manual solutions written in Step 3.

---

## Step 1 — Summarize the session

Write a concise summary covering:

```
## What was done
<bullet list of completed work — specific, with file:line or commit sha>

## Key decisions made
<bullet list — decisions that future agents need to know>

## What was discovered (non-obvious)
<constraints, surprising behavior, things that didn't work>

## Current state
<exact state of work — what's staged, what's unstaged, what's WIP>

## What to do next
<concrete next steps — specific enough that a fresh agent can continue>

## Open questions
<anything unresolved that needs human input>
```

---

## Step 2 — Write to `specs/HANDOFF.md`

Write the summary above to `specs/HANDOFF.md` (overwrite — only latest session matters).

Format:

```markdown
# Handoff — <YYYY-MM-DD HH:MM>

## What was done
<from summary>

## Key decisions
<from summary>

## Discoveries
<from summary>

## Current state
Branch: <branch>
Staged: <files or "none">
WIP: <files or "none">

## Next steps
<from summary>

## Open questions
<from summary>

## Context to reload
- .claude/docs/index.md
- .claude/docs/solutions/INDEX.md
- ~/.claude/docs/solutions/INDEX.md
```

---

## Step 3 — Merge learnings into solutions

For each item in "Key decisions" and "Discoveries":
- Does it belong in `docs/solutions/`? (Is it surprising? Non-obvious? Would a future agent repeat the mistake?)
- If yes → write it now (don't wait for `/compound`)
- If no → leave it in HANDOFF.md only

---

## Step 4 — Update global memory

For user-level preferences or behaviors learned this session:
- Write to `~/.claude/projects/<project>/memory/` if applicable
- Keep under 200 lines total per memory file

---

## Step 5 — Report

```
Compact complete.

Written: specs/HANDOFF.md
Solutions updated: N files
Memory updated: yes/no

Next session: read specs/HANDOFF.md first, then continue from "Next steps".
Claude Code auto-compact: active (handles within-session context automatically).
```

---

## Note on Claude Code built-in compaction

Claude Code automatically compresses prior messages when context approaches limits. The summary + remaining context is carried into the next context window — you don't need to do anything for within-session compaction.

This skill handles what built-in compaction does NOT do: **persisting state to disk for the next day**.
