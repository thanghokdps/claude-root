# dev

Build and fix the way the repo already does it, whatever your role: a lane router that decides how much ceremony a request needs, a feature loop that splits the work into slices and dispatches each to the role pack's engineer (`frontend`, `backend`, `agent`), a bug loop that reproduces before it fixes, and test-first. The stack-specific skills live in the role packs, which core's `repo-profile` hook enables per repo.

**For:** every developer. Install this one plugin and the plan, review and core skills come with it.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/coordinator` | The right workflow for a request is unclear. Classifies the intent (feature, bug, review, refactor, explore, security), picks the lane and dispatches. Runs on its own behind every plain-language request | `/coordinator add CSV export to reports` |
| `/feature` | A new capability, end to end: risk intake, lane, plan, build, review | "add dark mode to the settings page" |
| `/ticket` | A tracker ticket by id (GitHub, GitLab, Jira). Writes the contract into `docs/tickets/<id>/` (intent, spec, plan), builds through `/feature`, ships contract and code in one PR. Several ids run in parallel, one worktree each | `/ticket 412` · "làm song song ticket 412 413" |
| `/fix-bug` | Something is broken, failing or slow, including after earlier fixes did nothing. Builds a tight red loop first, then minimises, hypothesises, instruments, fixes and locks it with a regression test | "sửa mấy lần rồi vẫn lỗi" |
| `/tdd` | Building test-first, or a `PLAN.md` task has a verify command. One seam, one failing test, one minimal implementation per cycle | "implement task 3 of the plan, TDD" |
| `/resolve-question` | A plan, ticket or subagent has an open question. Answers facts from the repo with a `file:line` citation; asks the user only the high-impact choices, as options | "decide the small stuff yourself, only ask me the risky choices" |
| `/checkpoint` | Midway through a plan, or before a commit or PR. Progress against `PLAN.md` plus every quality gate (typecheck, lint, tests), pass or fail per gate | `/checkpoint` |

## Hooks (always on)

| Hook | Event | Does |
|---|---|---|
| `ticket-ledger` | prompt expansion; after Skill, Agent and Task calls | Records which skills and subagents ran on each branch, for `ticket-gate` |
| `ticket-gate` | before `git commit`, `git push` and PR creation | A ticket's code commit waits for the skills its `plan.md` names and for every `blocking` concern in `spec.md` to have a decision; its PR waits for `/verify-done` and `/review-checklist`. A skipped step is waived in writing: `skip /<skill>: <reason>` in `plan.md` |
| `test-lock` | before Edit, Write and Bash | While `/fix-bug` has locked the test that reproduces a bug, edits to that test are blocked, so the fix changes the code, not the test |
| `weakened-check` | before Bash | A commit that lowers the bar (a deleted test, a loosened assertion or validation, a loosened row in `CONSTRAINTS.md`) asks the user first |
| `ask-once` | prompt; after Edit and Write; before AskUserQuestion; on stop | Every question is asked before the first edit. Once the build has started, a question is turned into a `/resolve-question` debate and the choice is listed under **Decided for you**; a confirmation no rollback undoes (push, merge, deploy, delete) still reaches the user |
| `plan-recall` | prompt | An active `specs/*/PLAN.md` is recalled every turn (its next open task and recent status), so `/clear` or a compaction never loses the slice |
| `plan-gate` | on stop | A turn cannot end silently while an active `PLAN.md` still has an open task; set `**Status:** paused` to set a plan aside |
| `auto-decisions` | on stop | On a high-risk ticket worked without the user, every choice Claude made alone is listed for review |

## Depends on

`core`, `plan`, `review`, `ship` (and through them `progress`). `ship` comes along so a built feature can land: `/finish-branch`, `/write-migration`, `/ci-triage`.

## Install

```text
/plugin install dev@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
