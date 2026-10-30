# dev

Build and fix the way the repo already does it: a lane router that decides how much ceremony a request needs, a feature loop, a bug loop that reproduces before it fixes, test-first, and one skill per fullstack layer (endpoint, database, React feature, API client, design to UI).

**For:** developers. Install this one role and the plan, review and core skills come with it.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/coordinator` | The right workflow for a request is unclear. Classifies the intent (feature, bug, review, refactor, explore, security), picks the lane and dispatches. Runs on its own behind every plain-language request | `/coordinator add CSV export to reports` |
| `/feature` | A new capability, end to end: risk intake, lane, plan, build, review | "add dark mode to the settings page" |
| `/ticket` | A tracker ticket by id (GitHub, GitLab, Jira). Writes the contract into `docs/tickets/<id>/` (intent, spec, plan), builds through `/feature`, ships contract and code in one PR. Several ids run in parallel, one worktree each | `/ticket 412` · "làm song song ticket 412 413" |
| `/fix-bug` | Something is broken, failing or slow, including after earlier fixes did nothing. Builds a tight red loop first, then minimises, hypothesises, instruments, fixes and locks it with a regression test | "sửa mấy lần rồi vẫn lỗi" |
| `/tdd` | Building test-first, or a `PLAN.md` task has a verify command. One seam, one failing test, one minimal implementation per cycle | "implement task 3 of the plan, TDD" |
| `/api-endpoint` | A new or changed backend route (Next.js handler, Express/Hono, FastAPI): schema, session auth, permission on the specific resource, thin handler, stable error codes, the 200/400/401/404 test matrix | "thêm API endpoint tạo đơn hàng" |
| `/db-change` | A new table, column, index or relation, or a slow or leaking query (Drizzle, Prisma, Alembic). ERD and schema first, reviewed migration, owner-scoped repository functions, tests on a real engine | "query trả dữ liệu của user khác" |
| `/ui-feature` | A page, form, dialog or screen in React with no design to match: feature folder, typed fetchers, every state (loading, empty, error, optimistic rollback), accessibility, tokens, Testing Library tests, a browser check per viewport | "làm màn hình settings với form đổi mật khẩu" |
| `/api-client` | The frontend must call the backend, or the backend must call a third party from its OpenAPI spec: typed client, credentials from env, timeouts, retries for idempotent reads only, mocks | "tích hợp API thanh toán từ swagger này" |
| `/design-ui` | A page must match a Figma link, exported frames or a screenshot. Exports frames, maps variables to tokens, builds the design's components once as primitives, diffs screenshots at the frame size and narrow widths | "làm UI theo figma này" |
| `/resolve-question` | A plan, ticket or subagent has an open question. Answers facts from the repo with a `file:line` citation; asks the user only the high-impact choices, as options | "decide the small stuff yourself, only ask me the risky choices" |
| `/checkpoint` | Midway through a plan, or before a commit or PR. Progress against `PLAN.md` plus every quality gate (typecheck, lint, tests), pass or fail per gate | `/checkpoint` |

## Hooks (always on)

| Hook | Event | Does |
|---|---|---|
| `ticket-ledger` | prompt expansion; after Skill, Agent and Task calls | Records which skills and subagents ran on each branch, for `ticket-gate` |
| `ticket-gate` | before `git commit`, `git push` and PR creation | A ticket's code commit waits for the skills its `plan.md` names and for every `blocking` concern in `spec.md` to have a decision; its PR waits for `/verify-done` and `/review-checklist`. A skipped step is waived in writing: `skip /<skill>: <reason>` in `plan.md` |
| `test-lock` | before Edit, Write and Bash | While `/fix-bug` has locked the test that reproduces a bug, edits to that test are blocked, so the fix changes the code, not the test |
| `weakened-check` | before Bash | A commit that lowers the bar (a deleted test, a loosened assertion or validation) asks the user first |
| `auto-decisions` | on stop | On a high-risk ticket worked without the user, every choice Claude made alone is listed for review |

## Depends on

`core`, `plan`, `review` (and through them `progress`).

## Install

```text
/plugin install dev@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
