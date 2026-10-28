# Ticket contract — `docs/tickets/<id>/`

Committed with the code, in the same PR. `<id>` is the tracker's id as written (`412`, `ABC-123`). One folder per ticket; a follow-up ticket gets its own folder and links back.

| File | Answers | Written in | Changes after merge |
|------|---------|------------|---------------------|
| `intent.md` | Why: what the ticket asked, for whom | Step 2 | Never — a new ticket instead |
| `spec.md` | What: criteria, contract, test matrix | Step 2, ticked in Step 4 | Only by a later ticket, with a § Changes entry |
| `plan.md` | How: slices, files, waves, deviations | Step 2, deviations in Step 3 | Never |

## `intent.md`

```markdown
# <id> — <ticket title>

Ticket: <link> · Opened by: <reporter> · Read: <YYYY-MM-DD>

## The ticket (verbatim)
> <body, quoted as written; images linked>

## Outcome
- User: <who gains>
- Outcome: <what they can do after this, one sentence>
```

## `spec.md`

```markdown
# <id> — Spec

## Acceptance criteria
| # | Given | When | Then | Source |
|---|-------|------|------|--------|
| AC1 | <state> | <action> | <observable result> | ticket / decision <date> |

## Contract
<the endpoint, schema, event or UI state that changes — request/response shape, status codes, migration name>

## Out of scope
- <what this ticket does not do>

## Test matrix
| AC | Unit | Integration | E2E | Status | Evidence |
|----|------|-------------|-----|--------|----------|
| AC1 | yes | yes | no | planned | — |

## Cross-check
| AC | Design | API | App today | Gap |
|----|--------|-----|-----------|-----|
| AC1 | <frame / screenshot, states> | <endpoint, fields, auth, errors> | <route / component / service> | <none, or C#> |

## Concerns
| C# | Between | Severity | Owner | Question | Decision |
|----|---------|----------|-------|----------|----------|
| C1 | design ↔ API | blocking | backend | <question to paste as-is>. Recommended: <answer> | |

## Decisions
- <YYYY-MM-DD> <question> → <answer> (<who>)

## Changes
- none
```

Severity: `blocking` (cannot build without an answer), `decide` (buildable on the recommended answer, kept as an assumption), `note` (FYI). Decision stays empty until answered, then `<YYYY-MM-DD> <answer> (<who>)`, and is copied to § Decisions. `ticket-gate.sh` blocks a code commit while a `blocking` row has no Decision.

Status: `planned` · `in_progress` · `implemented` (evidence required: test path or command) · `changed` · `retired`.

## `plan.md`

```markdown
# <id> — Plan

Branch: <type>/<id>-<slug> · Lane: <tiny|normal|high-risk>

| Slice | Skill | Files | Green when |
|-------|-------|-------|------------|
| schema | /db-change | <paths> | <check> |

Waves: Wave 1 (parallel): <task> [files] | <task> [files] · Wave 2: …

## Deviations
- none
```
