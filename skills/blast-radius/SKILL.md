---
model: opus
effort: high
name: blast-radius
description: Change-impact analysis before merge — traces every caller, consumer, contract, job, and migration a change touches, scores the risk, flags untested paths, and demands a rollback plan. Answers "what else does this break?" with file:line evidence.
when_to_use: user says "blast radius", "impact analysis", "what does this break", "ảnh hưởng gì", "safe to merge?", before merging a PR, before a risky refactor, or when a change touches shared code
---

# Blast Radius

Map the ripple effect of a change **before** it merges. Every claim needs a `file:line` anchor. No speculation.

> **Not the same as `hooks/blast-radius-check.sh`.** That hook watches whether you edited a file outside the active `PLAN.md` `<files>` set — it polices scope creep during work. This skill analyses what a change *reaches* through the codebase. Same metaphor, different job.

---

## Stage 1 — Establish the change set

```bash
git diff --stat main...HEAD          # branch vs main
git diff --stat HEAD~1..HEAD         # last commit
git diff --stat                      # uncommitted
```

Pick whichever matches what the user is asking about. If ambiguous, ask once.

If the change is **proposed but not written yet**, take the described change and treat the named symbols as the change set.

Extract from the diff the list of **changed symbols** — exported functions, classes, types, routes, env vars, table names, event names, config keys. These are the seeds for Stage 2.

Print:

```
Change set: <n> files, <n> exported symbols touched
  src/auth/session.ts   — verifySession(), SessionOptions
  src/db/schema.sql     — users.role
```

---

## Stage 2 — Trace the impact

For **each** changed symbol, run the trace chain. Stop at the first layer that returns useful results, but always run the contract checks.

### 2a — Direct callers

```bash
rg -n --no-heading '\b<symbol>\b'
```

Record every hit as `file:line`, then **split the hits into production callers and test callers** — do not discard the tests. Test callers are the answer to "what goes red in CI when this changes", which is exactly what a pre-merge reader wants. They also feed Stage 2e.

Follow re-exports one hop: if a barrel file (`index.ts`, `__init__.py`, `mod.rs`) re-exports the symbol, trace the barrel's importers too — a barrel hides the real fan-out.

### 2b — Indirect consumers

These do not show up in a symbol grep. Check each explicitly:

| Consumer type | How to find it |
|---|---|
| Event / pubsub subscribers | grep the event name string, topic name, channel |
| Queue / background jobs | grep the job name, task name, cron registration |
| HTTP routes | is the symbol reachable from a route handler? |
| CLI commands | grep the command registration |
| Scheduled tasks | crontab, workflow yaml, scheduler config |
| Feature flags | grep the flag key |
| Serialized/persisted shapes | is this type written to DB, cache, or a queue payload? |

A changed field on a type that gets serialized into a queue is the classic silent breaker — in-flight messages have the old shape.

### 2c — Contract surfaces

Flag every hit here as **automatically elevated risk**:

- Public API request/response shapes (added, removed, renamed, or type-changed fields)
- DB schema: column add/drop/rename/type change, index change, constraint change
- Migrations that are not reversible
- Env vars / config keys added or renamed (deploy must ship config first)
- Anything exported from a package other repos consume
- Auth / authorization logic
- Wire formats: protobuf, GraphQL schema, OpenAPI spec

### 2d — Cross-boundary reach

Note when the trace crosses a module, package, or service boundary. Cross-boundary calls are the ones nobody on the changing team is watching.

### 2e — Test coverage probe

This is how the `test gap` factor gets measured. It is the heaviest weight in Stage 3, so it must be observed, never guessed.

For each affected node, search **only** test files for the symbol:

```bash
rg -l '\b<symbol>\b' -g '*.test.*' -g '*.spec.*' -g '*_test.*' -g 'test_*' -g '*_spec.*'
```

| Result | Test gap factor |
|---|---|
| One or more test files reference the symbol | does **not** fire |
| No test file references it | fires (`0.30`) |

Adjust the globs to the project's own convention — read `.claude/docs/test-strategy.md` first if it exists, since a project with `tests/` mirroring `src/` or with table-driven Go tests will not match the defaults above.

This is a reference check, not a coverage measurement: a test file mentioning the symbol is not proof the behaviour is covered. Treat "does not fire" as *not obviously untested*, and say so in `Not checked` when the distinction matters. If the project has a real coverage tool wired up (`stack.md` will say), prefer its output over this grep.

---

## Stage 3 — Score the risk

Score **each affected node**, then the change overall.

| Factor | Weight | Fires when |
|---|---|---|
| Test gap | 0.30 | Stage 2e found no test file referencing this node |
| Flow participation | 0.25 | Node sits on a critical path (auth, payment, data write, startup) |
| Security surface | 0.20 | Node name or body touches auth, token, password, secret, permission, crypto, session |
| Cross-boundary | 0.15 | Callers live in a different module/package/service |
| High fan-in | 0.10 | 5+ distinct call sites |

Weights sum to exactly `1.00`, so a node score is already bounded.

**Per-node level:**

| Score | Level |
|---|---|
| `0.00–0.29` | 🟢 low |
| `0.30–0.59` | 🟡 medium |
| `0.60–1.00` | 🔴 high |

**Overall level — count nodes, do not take the max.**

| Overall | Fires when |
|---|---|
| 🔴 high | An irreversible migration is in the change set · **OR** ≥1 node scores `≥0.60` **and** Stage 2c found a contract change · **OR** ≥3 nodes score `≥0.30` |
| 🟡 medium | Any Stage 2c contract change · **OR** ≥1 node scores `≥0.30` |
| 🟢 low | Everything else |

Why counting and not max: `test-gap 0.30 + flow 0.25 + security 0.20 = 0.75`, so under a max rule a **single** untested function on an auth path turns every change red. Since this skill runs mainly on `high-risk` lane changes — which are *defined* as auth, authz, migration, payment, contract — a max rule would return 🔴 almost every time, and a verdict that never varies gets ignored. Counting requires either breadth (3+ affected nodes) or a severe node **plus** a contract change before escalating.

Averaging is also wrong — it hides the one dangerous node in a crowd of safe ones. Report the per-node scores in full and let the counting rule decide the headline.

---

## Stage 4 — Report

```markdown
# Blast radius — <branch or change description>

**Overall: 🔴 high** — 1 node ≥0.60 (`chargeCard()`) plus a contract change (`POST /api/session`)
4 files changed · 17 affected nodes · 2 high · 5 medium · 6 untested

## Affected nodes

| Risk | Node | Location | Reached via | Factors |
|------|------|----------|-------------|---------|
| 🔴 0.72 | `chargeCard()` | `src/billing/charge.ts:88` | direct caller of `verifySession()` | test-gap, flow, security |
| 🟡 0.45 | `refund-worker` | `workers/refund.ts:23` | queue consumer of `payment.completed` | test-gap, cross-boundary |
| 🟢 0.15 | `AdminPanel` | `web/admin/Panel.tsx:14` | direct caller | fan-in |

## Contract changes

| Surface | Change | Breaks |
|---------|--------|--------|
| `POST /api/session` | `expiresAt` renamed → `expires_at` | any client parsing the old key |
| `users.role` | `varchar(20)` → enum | rows with values outside the enum |

## Untested paths

Stage 2e found no test file referencing these:

- `src/billing/charge.ts:88` `chargeCard()`
- `workers/refund.ts:23` `handleRefund()`

## Tests that reference the change set

These go red first in CI:

- `src/auth/session.test.ts:12,40` — `verifySession()`

## Required before merge

- [ ] Add test for `chargeCard()` — highest-risk untested node
- [ ] Confirm no in-flight `payment.completed` messages use the old payload shape
- [ ] Backfill or default `users.role` before the enum migration
- [ ] Ship config change for `SESSION_TTL` ahead of the deploy

## Rollback

| Step | Command | Reversible |
|------|---------|-----------|
| Code | `git revert <sha>` | yes |
| Migration | `<down migration command>` | **no — enum narrowing drops data** |

## Not checked
- Dynamic dispatch via string keys — grep cannot see these
- Test gap is a reference check (Stage 2e), not a coverage measurement
- <anything else you could not resolve>
```

**The `Rollback` section is mandatory.** If any step is irreversible, say so loudly — and per the Stage 3 table, an irreversible migration in the change set is on its own enough to make the overall verdict 🔴.

---

## Rules

- **Every node needs a `file:line`.** A node you cannot anchor goes under `Not checked`, not in the table.
- **Never guess a caller.** If grep found nothing, report zero callers and say the trace was grep-based.
- **State your trace method.** `rg`-based tracing misses dynamic dispatch, reflection, string-keyed registries, and DI containers. Say so in `Not checked`.
- **Do not review code quality.** Bugs and style are `/code-review`'s job. This skill answers reach and risk only.
- **Do not fix anything.** Report only. Fixing is a separate dispatch.
- **Do not pad the node list.** 15 well-anchored nodes beat 60 grep hits on a common word.

---

## Where this sits

```
implementation done
      ↓
/blast-radius    → what does this reach? safe to merge? — this skill
      ↓
/code-review     → is the changed code itself correct?
      ↓
/checkpoint      → do the quality gates pass?
```

If the verdict is 🔴 high, the change belongs in the `high-risk` lane — update `specs/<slug>/SUMMARY.md` `Lane:` accordingly, record the rollback commands in its `## Rollback` section, and add an `E00x` entry to `specs/<slug>/ESCALATIONS.md`. That entry defaults to deny-on-no-response, so it holds the work until a human decides. This skill itself does not block anything; only hooks can do that.

---

## Quick reference

```
/blast-radius                             # current branch vs main
/blast-radius HEAD~3..HEAD                # a specific range
/blast-radius src/auth/session.ts         # everything reachable from one file
/blast-radius if I rename users.role to users.role_id
```
