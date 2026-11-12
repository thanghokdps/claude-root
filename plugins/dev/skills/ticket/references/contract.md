# Ticket contract — `specs/<id>-<slug>/`

Personal, outside the repo: `specs/` is the repo's state dir the session start names (`~/.local/share/claude-harness/repos/<repo>-<hash>/specs/`). Never in `docs/tickets/` or any other repo path, never staged, never in the PR; the decisions reach the reviewer through the PR description (SKILL.md Step 4). `<id>` is the tracker's id as written (`412`, `ABC-123`); `<id>-<slug>` is the branch name without its type (`feat/412-due-date-filter` → `specs/412-due-date-filter/`), which is how the hooks find it. One folder per ticket; a follow-up ticket gets its own folder and names the earlier id.

| File             | Answers                                | Written in                   | Changes after merge                            |
| ---------------- | -------------------------------------- | ---------------------------- | ---------------------------------------------- |
| `intent.md`      | Why: what the ticket asked, for whom   | Step 2                       | Never — a new ticket instead                   |
| `spec.md`        | What: criteria, contract, test matrix  | Step 2, ticked in Step 4     | Only by a later ticket, with a § Changes entry |
| `plan.md`        | How: slices, files, waves, deviations  | Step 2, deviations in Step 3 | Never                                          |
| `plan-review.md` | Was the plan approved by a fresh agent | Step 2                       | Never                                          |

`specs/TICKETS.md` (beside the folders) holds one row per ticket, `| id | title | estimate | actual | note |`, filled in Step 4.

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

| #   | Given   | When     | Then                | Source                          |
| --- | ------- | -------- | ------------------- | ------------------------------- |
| AC1 | <state> | <action> | <observable result> | ticket / C<n> / decision <date> |

## Contract

<the endpoint, schema, event or UI state that changes — request/response shape, status codes, migration name>

## Out of scope

- <what this ticket does not do>

## Test matrix

| AC  | Unit | Integration | E2E | Status  | Evidence |
| --- | ---- | ----------- | --- | ------- | -------- |
| AC1 | yes  | yes         | no  | planned | —        |

## Cross-check

| AC  | Design                       | API                              | App today                     | Gap           |
| --- | ---------------------------- | -------------------------------- | ----------------------------- | ------------- |
| AC1 | <frame / screenshot, states> | <endpoint, fields, auth, errors> | <route / component / service> | <none, or C#> |

## Concerns

| C#  | Between      | Severity | Owner   | Question                                         | Decision |
| --- | ------------ | -------- | ------- | ------------------------------------------------ | -------- |
| C1  | design ↔ API | blocking | backend | <question to paste as-is>. Recommended: <answer> |          |

## Decisions

- <YYYY-MM-DD> <question> → <answer> (user)
- <YYYY-MM-DD> <question> → <answer> (agent) · why: <fact or rule, with citation> · revert: <what to change to undo it>

## Changes

- none
```

Severity: `blocking` (cannot build without an answer), `decide` (buildable on the recommended answer, kept as an assumption), `note` (FYI). Decision stays empty until answered, then `<YYYY-MM-DD> <answer> (<who>)`, and is copied to § Decisions. A `decide` concern built on the recommended answer gets an `(agent)` entry there, with `why:` and `revert:`. `ticket-gate.sh` blocks a code commit while a `blocking` row has no Decision or an `(agent)` entry lacks `why:` or `revert:`.

Status: `planned` · `in_progress` · `implemented` (evidence required: test path or command) · `changed` · `retired`.

## `plan.md`

```markdown
# <id> — Plan

Branch: <type>/<id>-<slug> · Lane: <tiny|normal|high-risk>

| Slice  | Skill                              | Files   | Green when |
| ------ | ---------------------------------- | ------- | ---------- |
| schema | /db-change (backend, if installed) | <paths> | <check>    |

Waves: Wave 1 (parallel): <task> [files] | <task> [files] · Wave 2: …

## Deviations

- none
```
