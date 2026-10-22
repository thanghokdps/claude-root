# dev

Build and fix: coordinator lane router, feature, fix-bug red loop, tdd, checkpoint gates.

## Install

```
/plugin marketplace add thanghokdps/claude-root
/plugin install dev@harness
```

Also installs: `core`, `plan`, `review`.

## Skills

| Skill | Does |
|-------|------|
| `/checkpoint` | Checks progress against the active PLAN.md and runs every quality gate — typecheck, lint, tests — reporting pass/fail per gate |
| `/coordinator` | Orchestration entry point — classifies any incoming prompt (feature, bug, review, refactor, explore, security) and dispatches it to the right specialized agent with the correct ceremony level |
| `/feature` | Implements a new feature end to end — risk intake, lane assignment, plan, build, review |
| `/fix-bug` | Diagnosis loop for bugs and performance regressions — build a tight red loop first, then minimise, hypothesise, instrument, fix, and lock it down with a regression test |
| `/tdd` | Drives implementation as a red → green loop — one seam, one failing test, one minimal implementation per cycle |

All plugins: [`../README.md`](../README.md).
