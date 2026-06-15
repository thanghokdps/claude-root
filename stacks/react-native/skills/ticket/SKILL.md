---
name: ticket
description: Full multi-agent pipeline for a feature ticket in flash-mobile-app. Runs pm-agent → architect-agent → developer-agent → reviewer-agent → qa-agent automatically. Use /ticket #<issue> <description>.
---

# Ticket — flash-mobile-app

Full 5-agent pipeline for implementing a feature ticket end-to-end.

## Usage
```
/ticket #<issue> <description>
```

Example:
```
/ticket #123 add swipe-to-dismiss on pending request cards
/ticket #456 fix crash when meal reservation list is empty
```

## Pipeline

```
pm-agent       → research + context gathering
    ↓
architect-agent → technical plan with waves
    ↓
developer-agent → implement per plan
    ↓
reviewer-agent  → APPROVED or CHANGES REQUIRED
    ↓ (if APPROVED)
qa-agent        → lint + types + tests + commit
```

## Steps

### Step 1 — Initialize
```
TaskCreate({ title: "pm-agent: research #<issue>",       status: "pending" })
TaskCreate({ title: "architect-agent: plan #<issue>",    status: "pending" })
TaskCreate({ title: "developer-agent: implement #<issue>", status: "pending" })
TaskCreate({ title: "reviewer-agent: review #<issue>",   status: "pending" })
TaskCreate({ title: "qa-agent: verify & commit #<issue>", status: "pending" })
```

Also create `specs/<issue-slug>/` with SUMMARY.md, TEST_MATRIX.md, ESCALATIONS.md from `.claude/templates/`.

### Step 2 — PM Agent
`TaskUpdate(pm-agent → in_progress)`

Dispatch `.claude/agents/pm-agent.md` with:
- Ticket number and description
- Project context from `.claude/docs/`

Collect research summary → `TaskUpdate(pm-agent → completed)`

### Step 3 — Architect Agent
`TaskUpdate(architect-agent → in_progress)`

Dispatch `.claude/agents/architect-agent.md` with:
- PM research summary
- Project context from `.claude/docs/`

Collect implementation plan → `TaskUpdate(architect-agent → completed)`

### Step 4 — Developer Agent
`TaskUpdate(developer-agent → in_progress)`

Dispatch `.claude/agents/developer-agent.md` (or implementer.md) with:
- Implementation plan
- Conventions from `.claude/rules/project-conventions.md`
- Stack context from `.claude/docs/stack.md`

Collect implementation → `TaskUpdate(developer-agent → completed)`

### Step 5 — Reviewer Agent
`TaskUpdate(reviewer-agent → in_progress)`

Dispatch `.claude/agents/reviewer.md` with:
- Git diff of changes
- Checklist from reviewer.md

If CHANGES REQUIRED → re-dispatch developer-agent, then re-review. Max 2 cycles.
If APPROVED → `TaskUpdate(reviewer-agent → completed)`

### Step 6 — QA Agent
`TaskUpdate(qa-agent → in_progress)`

Dispatch `.claude/agents/qa-agent.md`.

QA runs all checks, fixes surface issues, commits.
`TaskUpdate(qa-agent → completed)`

### Step 7 — Final
`TaskList` → show completed board to user.

## Auto-triggered skills (no need to call manually)

| When | Skill | Who triggers it |
|------|-------|----------------|
| Figma URL in prompt | `/figma-to-screen` | Coordinator (intent detection) |
| New component/screen created | `/gen-tests` | developer-agent (always, Step 4) |
| Before commit | `/verify-feature` | qa-agent (always, Step 1) |

These run automatically inside the pipeline — user does not need to type them.

## Rules
- Never skip the reviewer step
- Never let QA fix logic errors — those go back to developer-agent
- If architect finds a hard gate (auth, data loss) → escalate to user before proceeding
- Commit only after qa-agent approval — not during implementation
- developer-agent MUST generate tests for every new file before handing off to reviewer
