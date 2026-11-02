# 0005 — Hooks enforce the process; a skill alone is a reminder

**Status:** Accepted

## Context

In the first real ticket demo (27 Oct 2026) the model skipped the layer skills, wrote code itself instead of dispatching a cheaper subagent, and edited files through the shell so the lint hook never ran. Text in a skill is read once and forgotten under pressure.

## Decision

What must happen is checked by a hook, not only written in a skill:

- Always on (`core`, `dev`): `branch-guard` (no commits to main or environment branches), `edit-guard` (repo files change through Edit/Write so per-edit hooks run), `ticket-gate` with `ticket-ledger` (a ticket's commit and PR wait for the skills its plan names, `/verify-done` and `/review-checklist`), `secret-guard` (secret files are never read), `sensitive-path` (secrets, CI and deploy files ask first), `test-lock` (a bug's reproduction test stays as written during the fix), `step-limit` (a subagent past 90 tool calls stops and reports).
- With the role (`ship`): `release-gate` (a production mobile release ships only an approved `release/<version>` commit).
- Opt-in (`guards`): commit quality, scope gate, blast radius, run log, push evidence, session handoff.
- Hooks exit 0 or 2, never 1. A hint that should not block uses `additionalContext` or a permission `ask`.

## Consequences

- A skipped step shows up as a blocked commit with the reason, not as a surprise in review.
- Every gate has a written waiver (`skip /<skill>: <reason>` in `plan.md`), so the reason is on record.
- Hooks that block commits never arrive with a plain skill install: anything beyond the core gates is opt-in.

## Where

`plugins/core/hooks/`, `plugins/dev/hooks/`, `plugins/ship/hooks/`, `plugins/guards/hooks/`, tests in `scripts/test_*.py`.
