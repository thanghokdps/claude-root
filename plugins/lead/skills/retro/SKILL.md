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

## Step 2b — Settle the decisions agents made

Agents decide choices for the user mid-build (`/resolve-question`, dev, if installed) and record each with a `revert:` naming its files. Score them the way an estimate is scored:

```bash
python3 -I ${CLAUDE_SKILL_DIR}/scripts/settle-decisions.py .
```

One JSON line per decision ready to settle: `reverted` or `changed` (a later `revert`/`fix` commit on its files, in `evidence`), `kept` (14 days with neither), `unreadable` (`revert:` names no file). Append one line each to `.claude/docs/decisions.md`, keyed exactly as `key` so the next run skips it:

```markdown
- <today> · <status> · <key> · evidence: <sha> <subject> · lesson: <2–4 sentences>
```

- `reverted` / `changed`: the lesson says, in plain prose, what the decision assumed, what the evidence commit shows it got wrong, and one concrete rule for the next similar choice. Open the evidence commit before writing it; the commit says what changed, the lesson must not claim more.
- `kept`: `lesson: none`. `unreadable`: `lesson: revert: named no file` — a Hurt row, since nobody can roll it back.
- A reverted or changed share above 1 in 4 over the window is a Hurt row.

The debate reads the newest lessons back before its next choice of the same kind, so every word must earn its place.

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
