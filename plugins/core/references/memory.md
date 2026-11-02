# Memory rules

## Memory lives at `.claude/memory/`

```
.claude/memory/
├── MEMORY.md              # Index — ALWAYS loaded every session
├── user.md                # User profile, role, preferences
├── feedback/              # Corrections + validated approaches
│   └── YYYY-MM-DD.md
├── project/
│   └── context.md         # Goals, decisions, deadlines, constraints
├── commits/               # Auto-saved after each git commit
│   ├── YYYY-MM-DD.md
│   └── last-sync.txt      # Last commit hash (for team sync)
└── sessions/              # Session breadcrumbs
    └── YYYY-MM-DD.md
```

## When to save

| Trigger | Type | Where |
|---------|------|-------|
| User corrects your approach | feedback | `feedback/YYYY-MM-DD.md` |
| User confirms non-obvious approach worked | feedback | `feedback/YYYY-MM-DD.md` |
| Learn project goal / deadline / decision | project | `project/context.md` |
| `git commit` succeeds | project | `commits/YYYY-MM-DD.md` (auto via hook) |
| Session ends | project | `sessions/YYYY-MM-DD.md` (auto via hook) |
| Learn user role / preference | user | `user.md` |

## Feedback memory format

```markdown
---
name: feedback-<slug>
description: <one line — be specific about what pattern this covers>
metadata:
  type: feedback
---

<The rule itself — lead with the behavior to adopt or avoid>

**Why:** <The reason — past incident, user preference, project constraint>
**How to apply:** <When and where this kicks in>
```

## What NOT to save

- Code patterns, architecture, file paths — derivable from the code
- Git history — use `git log`
- Debugging solutions or fix recipes — the fix is in the code
- In-progress task state — use session notes
- Anything already in `CLAUDE.md`

## MEMORY.md index rules

- One line per entry: `- [Title](path) — one-line hook`
- Keep under 150 entries (lines > 200 are truncated)
- Date entries are most recent first
- Remove stale entries (memories > 30 days old that no longer apply)

## Team sync memory

When working in a team:
- Run `/sync-memory` at the start of each session
- Memory in `commits/` tracks YOUR commits — team commits are context-only
- `commits/last-sync.txt` stores the hash of your last synced commit
- If a teammate changed a file you're about to change → check their commit first

## Before acting on a memory

- File path memories: verify the file still exists (`ls <path>`)
- Function/flag memories: verify it still exists (`grep -r <name> src/`)
- A memory is "what was true when written" — not necessarily true now
- If memory conflicts with current code → trust the code, update the memory
