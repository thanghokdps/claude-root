# dev

Build and fix: coordinator lane router, feature, fix-bug red loop, tdd, design-ui from Figma, checkpoint gates — and the fullstack layer skills every developer uses: backend endpoint, database change, React feature, API integration.

## Install

```
/plugin marketplace add thanghokdps/claude-root     # GitHub (public, no VPN)
# or: /plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git   # GitLab (team: VPN + SSH key)
/plugin install dev@harness
```

Also installs: `core`, `plan`, `review`.

## Skills

| Skill | Does |
|-------|------|
| `/api-client` | Integrates an API — typed frontend fetchers to the app's backend, or a backend client for a third-party API from its spec, with timeouts, read-only retries, error mapping and no-network mocks |
| `/api-endpoint` | Adds or changes a backend endpoint (Next route handler, Express/Hono, FastAPI) — schema, auth, resource permission, thin handler, error codes, the 200/400/401/404 route matrix |
| `/checkpoint` | Checks progress against the active PLAN.md and runs every quality gate — typecheck, lint, tests — reporting pass/fail per gate |
| `/coordinator` | Orchestration entry point — classifies any incoming prompt (feature, bug, review, refactor, explore, security) and dispatches it to the right specialized agent with the correct ceremony level |
| `/db-change` | Changes the database (Drizzle, Prisma, Alembic) — ERD and schema first, reviewed migration, owner-scoped repository functions, real-engine tests |
| `/design-ui` | Turns a Figma link or mockup into UI: frames, every screen state, tokens, the design's components classified against the repo's UI library and built once as primitives, screenshot diff at the frame size and narrow widths |
| `/feature` | Implements a new feature end to end — risk intake, lane assignment, plan, build, review |
| `/ticket` | Works a ticket by id — writes `docs/tickets/<id>/intent.md`, `spec.md`, `plan.md` into the repo, builds through `/feature`, ships the contract in the same PR; several ids run in parallel, one worktree and PR each |
| `/fix-bug` | Diagnosis loop for bugs and performance regressions — build a tight red loop first, then minimise, hypothesise, instrument, fix, and lock it down with a regression test |
| `/ui-feature` | Builds a React feature — feature folder, typed fetchers, primitives, every state (loading, empty, error, optimistic rollback), a11y, tokens, Testing Library tests and a browser check at each viewport |
| `/resolve-question` | Answers an open question from the repo with a `file:line` citation before anyone guesses; asks the user only the real choices, as options |
| `/tdd` | Drives implementation as a red → green loop — one seam, one failing test, one minimal implementation per cycle |

All plugins: [`../README.md`](../README.md).
