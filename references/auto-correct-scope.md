# Auto-Correct Scope Rules

Four rules governing when an agent can fix code autonomously vs. when human confirmation is required.

## Rule 1 — Obvious bugs discovered during implementation

**Auto-fix allowed.** Examples: wrong query condition, off-by-one, typo in a variable name, missing null check for a value that is clearly always non-null.

## Rule 2 — Missing functionality clearly required by project standards

**Auto-fix allowed.** Examples: input validation on a public endpoint, error handling that the project's existing pattern mandates, logging that every other similar module has.

## Rule 3 — Issues blocking task completion

**Auto-fix allowed.** Examples: syntax error, missing import, missing dependency that is obviously correct.

## Rule 4 — Architectural judgment — NEVER auto-apply

**Requires human confirmation.** Examples:
- Schema or data model changes
- Public API contract changes (adding/removing/renaming fields)
- Security-sensitive logic (auth, authorization, encryption)
- Removing or weakening validation
- Cross-service contract changes

## Reporting Requirement

Every autonomous fix under Rules 1–3 must be documented in `specs/<slug>/SUMMARY.md` under `## Deviations`:

```
- [Rule N] Fixed <what> in <file:line> — <one sentence why>. Commit: <sha>
```

## Rollback Requirement

For high-risk work or any Rule 4 action proceeding after human approval, record the exact undo command in `specs/<slug>/SUMMARY.md` under `## Rollback` before marking the task complete. Reversibility is a precondition for autonomy.
