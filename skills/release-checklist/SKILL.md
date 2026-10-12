---
model: opus
effort: medium
name: release-checklist
description: Walks a release through a fixed checklist — scope frozen, gates green, migrations safe, release notes drafted, tag, deploy, smoke check, rollback ready — and stops on the first unmet item. Use when cutting a release, tagging a version, or deploying to staging/production.
when_to_use: cutting a release, tagging a version, deploying to staging or prod, end of sprint, "ship it"
---

# release-checklist — the release process, followed every time

**Invoke:** `/release-checklist <version> [staging|production]`

Project override: if the repo has `RELEASE.md` or `.claude/docs/release.md`, its steps come first; this list fills the gaps.

## Checklist — stop at the first ❌

| # | Item | How to verify |
|---|------|---------------|
| 1 | **Scope frozen** | List merged PRs/MRs since last tag: `git log --oneline <last-tag>..HEAD`. Anything unexpected → ask. |
| 2 | **Gates green** | CI on the release commit is green; run the project's typecheck/lint/test locally if CI is unavailable. |
| 3 | **Migrations safe** | Any migration in range → it passed `/write-migration` checks (reversible, no locking rewrite, backfill separate). |
| 4 | **Config & secrets** | New env vars / feature flags exist in the target environment — names only, never print values. |
| 5 | **Release notes** | Drafted from the merged PRs (user-facing changes first, known issues stated). Publish as an artifact if it is for stakeholders. |
| 6 | **Version + tag** | Version bumped where the project keeps it; annotated tag `git tag -a v<version> -m ...`. Push only after the user confirms. |
| 7 | **Deploy** | Use the project's deploy command; production needs explicit user confirmation first. |
| 8 | **Smoke check** | Hit the critical path on the deployed env (health endpoint, login, the headline feature). |
| 9 | **Rollback ready** | Write the exact rollback command (previous tag / redeploy / migration down) before declaring done. |

## Output

A table of the 9 items with ✅ / ❌ / n/a and the evidence for each, then the rollback command.

## Rules

- Tag push, deploy and anything production-facing need explicit user confirmation — this skill prepares, the human pulls the trigger.
- n/a must say why (e.g. "no migrations in range").
