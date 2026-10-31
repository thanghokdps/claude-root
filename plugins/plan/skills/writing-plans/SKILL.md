---
model: opus
effort: high
name: writing-plans
description: Converts an approved design doc (specs/<slug>/design.md) into a detailed PLAN.md with wave-organized tasks, file maps, and verifiable acceptance criteria. Run after /brainstorming.
when_to_use: an approved design.md with no PLAN.md yet, "write the plan", "lên plan từ design", "chia thành wave / task", turn this design doc into an ordered task list with verify commands
---

# Writing Plans

Convert an approved design into a concrete, executable PLAN.md that any agent can follow without additional context.

---

## Prerequisites

- `specs/<slug>/design.md` must exist and be approved by the user
- If it doesn't exist, run `/brainstorming` first

---

## Process

### Step 1 — Read and internalize the design

Read `specs/<slug>/design.md` and the relevant existing code. Understand:
- What files need to change and why
- What the layering/architecture constraints are
- What tests already exist

### Step 2 — Build the file map

List every file to create, modify, or delete. For each:
- Exact path (no globs)
- Action: create | modify | delete
- Layer: which architectural layer it belongs to

### Step 3 — Break into atomic tasks

Each task must be:
- **Completable in 2–5 minutes** by a focused agent
- **Independently verifiable** with a shell command
- **Assigned to a wave** (same-wave tasks must have disjoint files)

Follow the TDD pattern:
1. Write failing test
2. Verify it fails (`pytest ... --co` or run and expect failure)
3. Implement minimal code
4. Verify tests pass

The plan's last task keeps the project's knowledge base current: on a repo that had no source when planning began (a scaffold), it runs `/project-init` (core, if installed), verified by `ls CLAUDE.md .claude/docs/index.md`; otherwise it runs `/docs-sync` (core, if installed) on the branch.

### Step 4 — Write PLAN.md

Save to `specs/<slug>/PLAN.md` following the format in `${CLAUDE_PLUGIN_ROOT}/references/plan-format.md`:

- Front matter: goal, architecture, tech stack, status: draft
- Non-goals section
- Success criteria (checkboxes)
- File map table
- Tasks in `\`\`\`xml` blocks with `<task id wave files action verify done>` structure
- Risks and mitigations
- Status log with creation date

### Step 5 — Plan review

Spawn a plan-reviewer sub-agent with this prompt:

```
You are a plan reviewer. Do NOT implement anything.

Review this PLAN.md for:
1. Tasks that are too large (> 5 min each) — suggest splitting
2. File overlaps within the same wave — identify and fix
3. Missing test coverage — every modified behavior needs a verify command
4. Unclear actions — flag any action that is ambiguous
5. Unrealistic verify commands — must exit 0 within 60 seconds

Return: a list of issues (or "APPROVED" if none).
```

Revise the plan based on feedback. Repeat until APPROVED.

### Step 6 — Update PLAN.md status and hand off

Set `Status: active` in the plan header.

Say: "Plan ready. Run `/coordinator` or use `/executing-plans` to begin execution." (`/coordinator` is in dev — name it only if installed.)

---

## Rules

- Complete code examples in tasks, not pseudo-code
- Exact file paths — no "somewhere in app/"
- Every task must have a `verify` command that exits 0 on success
- No task should touch files already assigned to another task in the same wave
- Do NOT start implementing
