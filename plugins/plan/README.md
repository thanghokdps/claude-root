# plan

Design before code: take a project or feature from the documents and ideas you have to a design that survived hard questions and a plan Claude can build wave by wave.

**For:** architects, tech leads, and anyone starting something non-trivial. Each skill ends in a file (`docs/kickoff.md`, `specs/<slug>/design.md`, `PLAN.md`, `.claude/docs/glossary.md`, ADRs) that the build skills read.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/kickoff` | Starting a new project from documents the team already has (PRD, ERD, ADR, stack, API specs). Reads them into one canonical doc set, shows a coverage matrix, then grills only the gaps | "Đây là PRD và ERD, bắt đầu dự án mới" |
| `/brainstorming` | A feature idea with no design yet. Explores intent, proposes several approaches, asks one question at a time, writes `specs/<slug>/design.md` | "I want to build a real-time notification system" |
| `/grill` | A design, plan or decision needs hardening before anyone builds it. A relentless one-question-at-a-time interview until every branch is resolved. Fires only by hand | `/grill specs/notifications/design.md` |
| `/domain-model` | Terms keep shifting meaning, a design uses a word the code does not, or a decision deserves a written rationale. Records terms in `.claude/docs/glossary.md` and decisions as ADRs | "two people mean different things by 'order'" |
| `/codebase-design` | Designing or improving a module's interface, deciding where a seam goes, making code testable. The deep-module vocabulary other skills borrow | "where should the seam between billing and invoicing go?" |
| `/writing-plans` | An approved `design.md` exists. Turns it into `PLAN.md` with wave-organised tasks, file maps and a verify command per task | `/writing-plans` |

The design chain: `/kickoff` or `/brainstorming` → `/grill` → `/writing-plans` → build (`/tdd` in `dev`, if installed).

## Hooks

None.

## Depends on

`progress`.

## Install

```text
/plugin install plan@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
