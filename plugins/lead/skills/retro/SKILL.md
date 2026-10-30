---
model: opus
effort: medium
name: retro
description: Weekly engineering retro from real data — commits, merged PRs/MRs, reverts, CI failures, and specs/ escalations over a time window — ending with what to standardize next (CLAUDE.md rule, skill, hook, or checklist item) and who owns it. Use at the end of a week or sprint, or after an incident.
when_to_use: retro or weekly review, "what did we ship this week", end of sprint, after an incident or a rough week
---

# retro — what shipped, what hurt, what to standardize

**Invoke:** `/retro [since]` — default: last 7 days.

## Step 1 — Gather facts (no opinions yet)

```bash
git log --since="7 days ago" --author="$(git config user.email)" --oneline --no-merges
git log --since="7 days ago" --grep='^revert' -i --oneline
gh pr list --state merged --search "merged:>=$(date -v-7d +%F)" --author @me   # or: glab mr list --merged
```

Also read: `specs/*/ESCALATIONS.md` touched in the window, `specs/STATE.md`, `docs/solutions/` entries added this week, and the rows of `docs/tickets/README.md` whose `actual` was filled in the window (`/breakdown` writes the estimate, `/ticket` the actual; both dev / plan, if installed).

## Step 2 — Summarize

| Section | Content |
|---------|---------|
| Shipped | Merged PRs/MRs, one line each, user-facing first |
| Hurt | Reverts, red builds, rework (same file changed in 3+ commits), escalations |
| Worked | Workflows worth repeating — with the evidence |
| Estimates | Per shipped ticket: estimate → actual and the note. The ratio over the window (actual ÷ estimate midpoint) becomes the calibration line in `.claude/docs/team.md` § Estimation that the next `/breakdown` (plan, if installed) reads; a ticket off by more than ×2 is a Hurt row with its cause |

## Step 3 — Standardize (the point of the retro)

Pick at most three changes, each with an owner and a home:

- Rule that keeps being restated → `~/.claude/rules/` or the project `CLAUDE.md`
- Workflow done by hand twice → a skill
- Mistake a script could have caught → a hook
- Review comment that keeps recurring → a `/review-checklist` item (review, if installed)

Then run `/compound` so the learnings persist.

## Rules

- Facts before interpretation; every "hurt" item cites a commit, PR, or build.
- Three changes maximum — a retro that changes everything changes nothing.
