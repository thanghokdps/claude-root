---
model: opus
effort: medium
name: checkpoint
description: Checks progress against the active PLAN.md and runs every quality gate — typecheck, lint, tests — reporting pass/fail per gate. Use to confirm where a feature stands or before handing work off.
when_to_use: midway through a PLAN.md, before a commit or PR, or when the user asks how far along something is
---

# checkpoint — Check progress against plan, run quality gates

**Invoke:** `/checkpoint`

**When to use:** Mid-task to see what's done, what's left, and whether quality gates pass.

---

## Stage 1 — Load plan context

Check for plan file:
- `specs/<slug>/PLAN.md` — structured plan from `/feature`
- `.claude/memory/sessions/` — recent session notes
- `.claude/memory/commits/` — recent commits

If no plan exists → report that and skip to Stage 3.

## Stage 2 — Map done vs remaining

For each task in the plan:
- Mark `✅ Done` if there's a commit or session note covering it
- Mark `🔄 In progress` if work started but no commit yet
- Mark `⬜ Not started` if untouched

Use `git log --oneline -20` and recent session memory to verify.

Report:
```
Progress: X / Y tasks complete

✅ Done:
  - [task 1]
  - [task 2]

🔄 In progress:
  - [task 3] — started, no commit

⬜ Not started:
  - [task 4]
  - [task 5]
```

## Stage 3 — Run quality gates

Run in order, stop at first failure:

```bash
# 1. TypeScript (if TS project)
npx tsc --noEmit
# Target: 0 errors

# 2. Lint
pnpm lint   # OR npm run lint OR ruff check .
# Target: 0 warnings

# 3. Unit tests (fast)
pnpm test --run   # OR npx vitest run OR pytest -q
# Target: all pass

# 4. Type coverage (if eval exists)
pnpm eval:agent   # only if router/tools changed
pnpm eval:rag     # only if RAG changed
```

Report each gate: ✅ pass / ❌ fail (with error count).

## Stage 4 — Blockers

List any blockers:
- Failing quality gates
- Unresolved feedback memories that apply to current work
- Uncommitted changes that belong to a previous task
- Stale memory (last sync > 2 days on team project)

## Stage 5 — Recommendation

One of:
- `Continue` — all gates pass, next task is clear
- `Fix gates first` — quality gate failures must be resolved before continuing
- `Sync memory` — team project, memory is stale, run `/sync-memory` first
- `Clarify` — plan is ambiguous for next task, ask user
