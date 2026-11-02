---
effort: low
name: debt-ledger
description: Lists every `shortcut:` comment in the repo as a debt ledger — what was simplified, the limit it names, and the trigger to revisit it — and flags shortcuts that name no trigger. Read-only, one-shot. Use when you want to see the deliberate shortcuts and deferrals before they quietly become permanent.
when_to_use: list the shortcuts we took, "what did we defer", "tech debt ledger", "nợ kỹ thuật", "liệt kê shortcut", before a release or a scale-up, planning a cleanup sprint, /debt-ledger
---

# debt-ledger — Every deliberate shortcut, in one list

**Invoke:** `/debt-ledger [marker word]` — default marker: `shortcut`.

The kit's code-quality rule marks a deliberate shortcut as `shortcut: <the limit>, <when to upgrade>`. This collects them so a deferral cannot rot unnoticed. Reads and reports only; changes nothing.

## Step 1 — Scan

```bash
git grep -nE --untracked '(#|//|/\*|--|<!--) ?shortcut:'
```

Replace `shortcut` with the marker the user names (`/debt-ledger TODO`). Add the comment prefix your stack uses if it is not in the pattern. The prefix keeps prose that only mentions the convention out of the ledger; also drop hits that are not a deferral, such as a note about a keyboard shortcut.

**Done when:** every hit is either a ledger row or dropped for a stated reason.

## Step 2 — Report

One row per marker, grouped by file:

```markdown
## Debt ledger — <repo>

### `src/rate_limit.py`
- `:42` in-memory counter. **Limit:** one process. **Upgrade:** when we run more than one worker.
- `:88` fixed 60 s window. **Limit:** bursts at the window edge. **Upgrade:** — `no-trigger`

<N> markers, <M> with no trigger.
```

Take the limit and the trigger straight from the comment. A marker that names no upgrade trigger gets `no-trigger`: those are the ones that silently become permanent. If the user wants an owner per row, add `git blame -L<line>,<line> -- <file>`.

Nothing found: `No shortcut debt. Clean ledger.`

## Rules

- Never edit code or comments from this skill. To keep the ledger, write it to a file only when the user asks.
- Never estimate how much a shortcut "saved": there is no unbuilt version to compare against.
