# How I work with Claude — Thang

One page. Guardrails and favorite workflows; the detail lives in the kit.

## Daily loop
1. One ticket = one session (worktree if another ticket is in flight). Resume, don't re-explain.
2. Paste the ticket → plan mode → approve the plan → implement → steer the diff with hunk comments.
3. Tests run, not trusted. Bad edit → `Esc Esc` rewind.
4. `/review-checklist` on my own diff → PR with what / why / how tested.
5. `/loop 15m` babysits the PR; red build → `/ci-triage`. GitLab repos get an automatic MR review from `templates/gitlab-ci/claude-review.gitlab-ci.yml`.

## Lanes
- tiny → just do it. normal → plan mode. high-risk (auth, data, migration, providers, contracts, `.claude/`) → `specs/<slug>/`, I confirm, `/code-review ultra` before merge.

## Favorite prompts
- "Explain how <feature> works, then list two claims I can verify by reading the code."
- "Reproduce <bug> as a failing test before touching the fix."
- `ultrathink` — only on the one gnarly bug, not the whole session.

## Guardrails
- Claude never pushes to main, force-pushes, deploys, or runs migrations on shared DBs — it prepares, I pull the trigger.
- No secrets in prompts, logs or commits. No AI trailers in commits.
- If Claude can't say "done when <check>", the task isn't ready.

## Kit map
`/coordinator` routes · `/brainstorming` → `/grill` → `/writing-plans` design · `/tdd` · `/fix-bug` · `/verify-done` · `/review-checklist` · `/finish-branch` · `/ci-triage` · `/release-checklist` · `/write-migration` · `/blast-radius` · `/compact` · `/compound` · `/retro` · `/diagnose-session`
