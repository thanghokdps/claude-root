# plan

Design before code: brainstorming, grill, domain-model, codebase-design, writing-plans → PLAN.md.

## Install

```
/plugin marketplace add thanghokdps/claude-root
/plugin install plan@harness
```

Also installs: `progress`.

## Skills

| Skill | Does |
|-------|------|
| `/brainstorming` | Design-first brainstorming session before any implementation |
| `/codebase-design` | Shared vocabulary for designing deep modules — a lot of behaviour behind a small interface, placed at a clean seam |
| `/domain-model` | Builds and sharpens the project's ubiquitous language — challenges fuzzy terms, cross-checks vocabulary against the code, and records resolved terms in .claude/docs/glossary.md and hard-to-reverse decisions as ADRs |
| `/grill` | Relentless one-question-at-a-time interview that stress-tests a plan, design, or decision until every branch of the decision tree is resolved |
| `/writing-plans` | Converts an approved design doc (specs/<slug>/design.md) into a detailed PLAN.md with wave-organized tasks, file maps, and verifiable acceptance criteria |

All plugins: [`../README.md`](../README.md).
