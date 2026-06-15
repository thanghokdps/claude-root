---
description: Full multi-agent pipeline — PM → Architect → Wave Executor (parallel) → Reviewer → QA — for a development ticket.
argument-hint: "[#issue-number] brief description"
---

# Ticket Workflow Orchestrator

**Ticket:** $ARGUMENTS

---

## Phase 1 — PM Agent (Research)

TaskCreate: "PM: research #<issue>"

Spawn `pm-agent`:
```
Agent({
  prompt: "Research ticket requirements. Read .claude/docs/index.md first.

Ticket: $ARGUMENTS

Deliverable:
- Affected modules/packages
- Existing code to reuse (file:line)
- Risks (shared package change? public contract?)
- Open questions",
  subagent_type: "general-purpose"
})
```

Save Research Brief → TaskUpdate completed.

---

## Phase 2 — Architect Agent (Wave Plan)

TaskCreate: "Architect: plan #<issue>"

Spawn `architect` agent:
```
Agent({
  prompt: "Produce a wave-organized implementation plan.

Ticket: $ARGUMENTS

Research Brief:
<Phase 1 output>

REQUIRED output format:

## Wave Plan

| Task | Wave | Files | Model | Verify |
|------|------|-------|-------|--------|
| T1.1 | 1 | src/... | haiku | <test command> |
| T2.1 | 2 | src/... | sonnet | <lint + typecheck command> |

Rules:
- Same wave = disjoint file sets, zero dependencies between tasks
- haiku for: tests, simple types, constants, mechanical tasks
- sonnet for: complex logic, hooks with state, integration
- Every task needs an exact verify command that exits 0",
  subagent_type: "general-purpose"
})
```

Parse Wave Plan. Save it. TaskUpdate completed.

---

## Phase 3 — Wave Executor

TaskCreate per wave task (all start as "pending").

**Execute wave by wave. For each wave N:**

1. Print a sentence naming the parallel tasks, then print the full status table:

```
T001 and T002 running in parallel. Updated pipeline status:

| Task | Status |
|------|--------|
| T001 | 🔵 Running (sonnet) |
| T002 | 🔵 Running (haiku) |
| T003 | ⬜ Waiting on T001 |
| T004 | ⬜ Waiting on T001+T002 |
```

2. **Dispatch ALL wave N tasks in ONE message** (`run_in_background: true`)
3. Print: `* Waiting for N background agents to finish`
4. As each agent completes → narrate inline + reprint updated table:

```
Agent "T001 <description>" completed · 3m 45s
T001 done ✅. Spawning T003 now. Still waiting on T002 before I can start T004.

| Task | Status |
|------|--------|
| T001 | ✅ Done |
| T002 | 🔵 Running (haiku) |
| T003 | 🔵 Running (sonnet) |
| T004 | ⬜ Waiting on T002 |
```

5. All wave N tasks ✅ → advance to Wave N+1

Status cell values: `✅ Done` · `🔵 Running (sonnet)` · `🔵 Running (haiku)` · `⬜ Waiting on TXxx` · `❌ Failed`

---

## Phase 4 — Reviewer Agent

TaskCreate: "Reviewer: review #<issue>"

Spawn `reviewer` agent:
```
Agent({
  prompt: "Review git diff. Output APPROVED or CHANGES REQUIRED.

Ticket: $ARGUMENTS

Check:
1. Correctness (logic bugs, null handling, async/await)
2. TypeScript (no any, props typed, return types)
3. Code quality (no debug logs, no dead code, no duplicates)
4. Test coverage (paired test file present for every changed impl file?)
5. Convention violations (.claude/docs/conventions.md)

Format: file:line — severity — finding — fix
Output APPROVED if clean.",
  subagent_type: "general-purpose"
})
```

**If CHANGES REQUIRED:**
- Re-dispatch affected wave tasks with fix instructions
- Max 2 fix loops → then BLOCKED

---

## Phase 5 — QA Agent

TaskCreate: "QA: verify & commit #<issue>"

Spawn `qa-agent`:
```
Agent({
  prompt: "Run checks, fix surface errors, commit.

Ticket: $ARGUMENTS

Steps:
1. Run lint, typecheck, tests for affected workspaces
2. Fix surface errors only (unused imports, missing types) — do NOT change logic
3. Verify no console.log/debugger in staged files
4. Commit using project commit convention from CLAUDE.md

Output QA Report.",
  subagent_type: "general-purpose"
})
```

---

## Final Summary

```
# ✓ Ticket Complete — $ARGUMENTS

| Phase | Agent | Status |
|-------|-------|--------|
| Research  | PM Agent       | ✅ |
| Plan      | Architect      | ✅ |
| Implement | Wave Executor  | ✅ |
| Review    | Reviewer       | ✅ |
| Ship      | QA Agent       | ✅ |

Commit: `<hash>`
```

TaskList → show completed board.
