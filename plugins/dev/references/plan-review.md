# Plan review and two-tier slice review

Read by `/feature` (Stage 2 and Stage 3) and `/ticket` (Step 2). Adapted from obra/superpowers `subagent-driven-development` (spec review before quality review) and chaseai-yt/claudex-loop (plan verdicts bound to the plan's hash, round cap).

Once the build starts the user is not asked again, so a plan error found after the code exists costs the whole slice. The agent that wrote the plan is the worst one to check it: its context has turned assumptions into facts. So the plan is reviewed by an agent that has read none of this conversation, and each slice by two agents with one lens each.

## Plan review

Runs after the plan is written and before the first slice, on the normal and high-risk lanes. Tiny lane: skip.

1. **Dispatch** one fresh `Agent` on `model: "opus"` (`~/.claude/rules/model-cost.md`: a wrong plan is expensive). The brief carries the plan path, the repo root, the lane and the user's request in one sentence. Nothing from this session's reasoning: a reviewer handed the planner's arguments validates them. The prompt opens:

   > You did not write this plan and have not seen the conversation that produced it. Read `<plan path>` and the code it names. For every task, check: the files exist or the plan creates them; the `verify` command runs here and fails today; the contract it states matches the callers you can find (`grep` them); nothing a task depends on is missing from an earlier task; no success criterion is untestable. Return one verdict — `APPROVED` (no finding changes what gets built), `REVISE` (findings, each with `path:line` and the task it affects) or `BLOCKED` (a fact you cannot settle from the repo: name it and who can) — then the findings. Cite a line for every claim; a finding without a citation is dropped.

2. **Arbitrate.** Open every cited line. A citation that does not say what the reviewer claims is dropped, with a one-line reason in the log. `REVISE`: change the plan for every finding that survives, then search the plan for every passage that still states the old behaviour (acceptance criteria included) and change those too; send the revised plan to a fresh reviewer. `BLOCKED`: the named fact goes to `/resolve-question`; a fact only the user can answer is asked now, before any code, since this is still the up-front phase.
3. **Cap: 2 rounds.** A plan still `REVISE` after round 2 is built with the open findings listed in the log under `## Open`, each with the arbitration; they also appear under **Decided for you**. Never retitle an unreviewed or disputed plan as approved.

### Log

`/feature`: `specs/<slug>/PLAN-REVIEW.md`. `/ticket`: `docs/tickets/<id>/plan-review.md`, committed with the code (the reviewer of the PR reads it next to the diff; `ticket-gate.sh` blocks a code commit until it says `Verdict: APPROVED`, waiver `skip plan-review: <reason>` in plan.md § Deviations).

```markdown
Verdict: APPROVED
Rounds: 2/2
Plan: docs/tickets/412/plan.md @ 3f9a1c2

## Round 1 — REVISE
- T2 `src/api/rename.ts:14` — route checks `ownerId`, plan assumed `teamId` → plan T2 contract changed to ownerId
- T3 — `verify` command `pnpm test rename` matches no test file → renamed to `pnpm test -- rename.spec`
- dropped: "T1 migration locks the table" — `prisma/migrations/…/migration.sql:3` adds a nullable column, no lock

## Round 2 — APPROVED

## Open
- none
```

`Plan: … @ <short sha256 of the plan file>`: a plan edited after approval is unreviewed again; recompute (`shasum -a 256 <plan> | cut -c1-7`) and re-run one round when it differs.

## Two-tier slice review

Each slice an engineer returns (Stage 3) is reviewed twice, sequentially, by fresh agents: **spec compliance** first, **code quality** only once spec passes. Reviewing the quality of code that builds the wrong thing is wasted; one agent asked for both lenses reads clean code as compliant code.

Record `BASE=$(git rev-parse HEAD)` before dispatching the engineer. Hand each reviewer a file, not pasted text: `git diff -U10 $BASE..HEAD > <specs or ticket dir>/review-<slice>.diff` (plus `git diff --stat`), so the diff never enters this session's context.

| Tier | Model | Gets | Asks | Returns |
|------|-------|------|------|---------|
| 1 — spec | `opus` | the slice's brief (contract, files, test, done check) and the diff file | does the diff do exactly what the brief says — nothing missing, nothing extra; does the done check pass for the reason the brief names | `SPEC ✅` or `SPEC ❌` + each gap as `brief says … / diff does …` with `path:line` |
| 2 — quality | `opus` | the diff file and the repo's rules (`.claude/rules/`, `CLAUDE.md`) | correctness bugs, error handling lost or added, validation at boundaries, tests that assert behaviour not implementation, dead code | findings as `path:line — Critical/Important/Minor — case that fails — fix` |

Both stay on `opus` (`model-cost.md`: review of a cheaper model's diff stays on Opus). A one-file mechanical slice may skip tier 2 when tier 1 passed and the slice's `verify` ran green; say so in the status table.

Rules:
- Never tell a reviewer what not to flag ("the plan chose", "at most Minor"): that is pre-judging. Let it raise the finding and arbitrate with the cited line.
- `SPEC ❌`, or any Critical or Important finding: the engineer that wrote the slice fixes it (resume that agent), then the same tier re-reviews the fix diff only. Cap: 3 fix rounds per slice; past the cap the slice goes back to this session to re-plan, not to a fourth retry (`model-cost.md`).
- A finding on code the slice did not touch is not the slice's: note it under `## Adjacent` in the plan, never fix it in the slice.
- Every verdict goes in the status table: `✅ Done (spec ✅, quality clean)` · `✅ Done (spec ✅, 1 Minor parked)` · `🔁 Fix round 2/3`.
