# Wave Parallelism Rules

How to organize and execute tasks in parallel waves.

## Waves vs. dynamic workflows

| | Wave parallelism (Agent tool) | Dynamic workflows (`ultracode`) |
|---|---|---|
| Who holds the plan | Claude's context window | A JS script the runtime executes |
| Scale | 2–8 parallel agents | Up to 16 concurrent, 1000 total per run |
| Intermediate results | Land in Claude's context | Stay in script variables |
| Resumable | No | Yes (same session) |
| When to use | In-session, results needed in context | Codebase-wide, worth saving/rerunning |

If the task needs more agents than fit in one context window, or the orchestration is worth rerunning → use a dynamic workflow with the `ultracode` trigger instead.

## Core Concept

Tasks are organized into sequential **waves**. Same-wave tasks execute in parallel. Wave N+1 must wait for wave N to fully complete and verify.

## Invariants (never violate)

1. **No file overlap** between tasks in the same wave
2. **All tasks in a wave must pass verification** before advancing
3. **Each task gets its own isolated agent context** — no shared state
4. **All parallel Agent calls happen in ONE message** with `run_in_background: true` — sending them in separate messages makes them sequential
5. **Results are collected and committed before the next wave starts**
6. **Model selection**: sonnet for complex logic, haiku for mechanical tasks (tests, simple CRUD)

## Wave Planning Template

```
Wave 1 (parallel): task-A [files: a.py, b.py] | task-B [files: c.py, d.py]
Wave 2 (sequential): task-C [depends on A+B] [files: e.py]
Wave 3 (parallel): task-D [files: f.py] | task-E [files: g.py]
```

## Collection Protocol (after each wave)

1. Verify all wave tasks returned PASS
2. Record commit sha for each task
3. Note any deviations in `specs/<slug>/SUMMARY.md`
4. Only then initiate the next wave

## Optimization

Single-task waves skip parallel machinery. Run directly in the main thread — no agent spawn overhead unless context budget requires it.

## Abort Condition

If any task in a wave returns FAIL:
1. Do not advance to the next wave
2. Fix the failing task
3. Re-verify the entire wave before proceeding
