---
model: opus
effort: high
name: feature
description: Implements a new feature end to end — risk intake, lane assignment, plan, build, review. Use when the user asks to add or build a feature rather than fix something broken.
when_to_use: a new capability is requested, or /coordinator classifies the intent as feature work
---

# feature — Implement a new feature

**Invoke:** `/feature <description>`

**What it does:** Risk intake → (research) → plan → build → review → commit

Work that has a tracker id goes through `/ticket` instead: it writes the contract to `docs/tickets/<id>/` (committed, unlike `specs/`) and then runs this skill with that plan.

This skill is the supervisor: it plans, splits the feature into slices, dispatches each slice to the role pack's engineer (Stage 3), reviews and integrates. It writes no slice itself when a pack is enabled.

---

## Stage 0 — Risk intake

Evaluate the request against the 10-flag checklist:

| Flag | Examples |
|------|----------|
| Auth / authorization | login, JWT, roles, permissions |
| Data model change | schema migration, new table/collection |
| External provider | new SDK, 3rd-party API, payment, AI model |
| Public contract change | REST endpoint rename, breaking type change |
| Audit / security | sanitization, validation removal, PII |
| Cross-platform impact | shared lib, monorepo, mobile + web |
| Existing behavior change | modifies path already covered by tests |
| Weak test coverage | area with < 50% coverage |
| High-blast file | config, shared middleware, CI pipeline |
| Multi-domain effect | touches 4+ modules or services |

Assign lane:
- **tiny** (0–1 flags): skip to Stage 3, direct edit
- **normal** (2–3 flags): run Stage 1 (research) + Stage 2 (plan)
- **high-risk** (4+ flags or hard gate): full chain — ask user for scope confirmation first

Output `LANE:` and `CONFIDENCE:` before proceeding.

### Open questions — every lane, before the first edit

List what the request leaves open: scope (what is in and out), the data it stores, what the user sees or gets back, where it surfaces, anything the repo answers two ways. Any open point → ask them all now, in one `AskUserQuestion` call (2–4 options each, the recommended one first with what it changes), and stop until answered. None → write `No open questions: <why the request already answers them>` and go on. The tiny lane skips research and the plan, never this step: a feature built on a guess is rebuilt.

### Hard gates (always high-risk, ask user first)
- auth / authorization
- data migration / schema change
- audit / security
- public API contract change
- high-blast file (config, CI, shared middleware)

## Stage 1 — Research (normal + high-risk only)

Answer before writing any code:
1. Does this already exist in the codebase? (`grep -r <keyword> src/`)
2. What's the lightest path: reuse existing code → adapt → build new?
3. What files will be touched? (estimate blast radius)
4. Are there tests covering the area? (`find . -name "*.test.*" | xargs grep -l <module>`)

Write findings to `specs/<slug>/research-brief.md` (high-risk) or keep inline (normal).

## Stage 2 — Plan (normal + high-risk only)

Write a step-by-step plan:
- Each step: 1 atomic action (write test → verify fail → implement → verify pass)
- Include exact commands with expected outputs
- List files to create + modify
- Flag any high-blast files with `⚠️`

For high-risk: save plan to `specs/<slug>/PLAN.md` and show user before building.

Then the plan is reviewed by an agent that has not seen this conversation (`${CLAUDE_PLUGIN_ROOT}/references/plan-review.md`): one fresh `opus` agent reads the plan against the code and returns `APPROVED`, `REVISE` or `BLOCKED` with a `path:line` per finding; at most 2 rounds, log in `specs/<slug>/PLAN-REVIEW.md`. A `BLOCKED` fact only the user can answer is asked now — this is still the up-front phase. No slice is dispatched before the log says `Verdict: APPROVED` or lists the open findings.

## Stage 3 — Build

Follow the plan step by step.

A feature is built as slices, in this order and one slice green before the next. Each slice belongs to one role pack and is dispatched to that pack's engineer with `Agent` (`subagent_type` from the table, `model: sonnet`) and a brief the engineer has nothing left to decide from: the contract (types, error codes), the files, the test to make pass, the done check (`model-cost.md`). The engineer runs the pack's skill. Its diff is reviewed in two tiers by fresh agents (`${CLAUDE_PLUGIN_ROOT}/references/plan-review.md` § Two-tier slice review): spec compliance against the brief first, code quality only once spec passes; a `SPEC ❌` or a Critical/Important finding goes back to the same engineer, 3 fix rounds at most. This session arbitrates the findings; it does not review the diff inline.

| Slice | Engineer | Runs | Green when |
|-------|----------|------|------------|
| tables, columns, queries | `backend:backend-engineer` | `/db-change` (backend, if installed) | migration applies, repository tests pass on the real engine |
| contract + endpoint | `backend:backend-engineer` | `/api-endpoint` (backend, if installed) | schema exported, route matrix passes (200 · 400 · 401 · 404 other user's) |
| third-party API the server calls | `backend:backend-engineer` | `/api-client` (backend, if installed) | tests pass with no network |
| web screen and states | `frontend:frontend-engineer` | `/ui-feature`, `/design-ui` first when there is a design (frontend, if installed) | Testing Library tests pass, browser check at every viewport |
| mobile screen | `mobile:mobile-engineer` | `/mobile-feature` (mobile, if installed) | tests pass, simulator check |
| agent tool, graph, HITL, prompt | `ai:ai-engineer` | `/agent-feature` (ai, if installed) | `/agent-verify-turn` on a real turn |
| chat surface: CopilotKit / AG-UI client, tool render, HITL card | `ai:ai-engineer` | `/agent-frontend`, `/agent-design-ui` (ai, if installed) | e2e on a recorded AG-UI stream |
| CI, container, infra | `devops:devops-engineer` | `/pipeline`, `/container`, `/infra-change` (devops, if installed) | plan reviewed, applied with approval, rollback named |

**Which pack owns a slice that touches two roles:** the pack of the *contract* the slice implements, not the language it is written in — whoever is paged when it breaks. A CopilotKit chat component is React but implements AG-UI, so it is `ai`'s; a settings page in the same Next app is `frontend`'s. A Prisma migration under a Next API route is `backend`'s. An EAS build is a store release (`ship`'s `release-gate`), not `devops`'s.

Skip a slice the feature does not need, and say so in the plan. The repo profile (`REPO PROFILE:` at session start) lists the packs enabled here; a slice whose pack is not enabled is built in this session with the table's "Green when" as its check, and the plan says so.

If the plan has 3 or more tasks/waves, print a status table before starting and update it after each task completes:

```
Building N tasks across M waves. Current status:

| Task | Status |
|------|--------|
| T1.1 | 🔵 Running (sonnet) |
| T1.2 | 🔵 Running (haiku) |
| T2.1 | ⬜ Waiting on T1.1+T1.2 |
| T3.1 | ⬜ Waiting on T2.1 |
```

After each task: narrate completion + reprint table immediately.
Status values: `✅ Done (spec ✅, quality clean)` · `🔵 Running (sonnet/haiku)` · `🔍 Review tier 1/2` · `🔁 Fix round n/3` · `⬜ Waiting on Txx` · `❌ Failed`

Rules:
- Run quality gates after each logical chunk: `npx tsc --noEmit`, lint, relevant tests
- If a step fails: diagnose root cause before moving on (don't hack around)
- If scope creep detected: stop and report to user, don't just keep going

## Stage 4 — Review

Every slice has passed its two-tier review by now; this stage checks the whole branch, once:
1. Does the branch match the plan — every task done, every § Deviations entry explained, every parked finding listed?
2. Any security issues across slices? (secrets, injection, unvalidated input at boundaries)
3. Any TypeScript errors or lint warnings?
4. Any dead code or accidental debugging artifacts?

For high-risk: one fresh reviewer agent on `opus` gets the whole-branch diff file (`git diff -U10 <base>..HEAD`) and the plan: "Review for correctness bugs across slices only — a contract one slice exports and another consumes differently, an error one slice raises and another swallows. Focus: [the plan's § Risks]."

Then `/docs-sync`: the routes, layers, commands and conventions this feature added go into `.claude/docs/` and `CLAUDE.md` in the same branch, so the next session does not rescan for them.

## Stage 5 — Commit

```bash
git add <specific files>
git commit -m "<type>: <what and why in one line>"
```

After commit: `save-commit-memory.sh` hook fires automatically and saves to memory.

---

## Confidence escalation rules

Every question goes to the user before the first code edit. After that the user is not asked: an open question mid-task goes through `/resolve-question`, which answers facts from the repo and settles choices by a subagent debate (`${CLAUDE_PLUGIN_ROOT}/references/auto-decisions.md`), recorded in the plan's § Decisions and listed under **Decided for you** in the final report.

Debate, never stop, when mid-task:
- Confidence drops below medium
- A hard gate is discovered (the debate adds an opus red team)
- Scope needs to expand beyond the original plan
- A teammate's recent commit conflicts with the planned approach (check `memory/commits/`)

Only an action no rollback undoes (push, merge, deploy, delete data) waits for the user's yes.
