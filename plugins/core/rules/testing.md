---
paths:
  - "**/*.{test,spec}.{ts,tsx,js,jsx,mjs}"
  - "**/__tests__/**"
  - "**/tests/**"
  - "**/test_*.py"
  - "**/*_test.{py,go}"
---

# Testing rules

## Quality gate order (always run in this sequence)

```bash
# 1 — TypeScript (if applicable) — blocks everything else
npx tsc --noEmit

# 2 — Lint
pnpm lint   # OR npm run lint OR ruff check . OR golint ./...

# 3 — Unit tests
pnpm test --run   # OR npx vitest run OR pytest -q OR go test ./...

# 4 — Integration / eval (only if relevant area changed)
pnpm eval   # OR pytest -m integration
```

Target: 0 errors, 0 warnings, all tests pass.

## What to test

- Test the behavior, not the implementation
- Cover: happy path, boundary conditions, error conditions
- Do NOT test: internal helper functions with no public surface
- Do NOT mock what you can test for real (mocks hide integration bugs)

## Test granularity

- **Unit tests** — stateless utilities, pure functions: fast, no I/O
- **Integration tests** — test against real DB, real file system, real API (where practical)
- **Eval tests** — LLM routing or retrieval accuracy: run only when that area changes

## Where tests live

- **The repo already has tests → follow its convention**, whatever it is (`__tests__/` folders, a separate `tests/` tree, or `*.test.ts` beside the file). Detect it from the existing files, the test runner's `include`/`testMatch`, and `.claude/docs/test-strategy.md`; the pattern most existing tests use wins. Never introduce a second layout.
- **No tests yet → the user picks**, through `AskUserQuestion` (numbered options without the tool), then the choice is recorded in `.claude/docs/test-strategy.md` and the runner config:
  1. `__tests__/` next to the code — `src/server/orders/__tests__/service.test.ts`. Tests stay with the module they cover and the source folder lists only source. Recommended for TS/JS apps.
  2. A separate `tests/` folder outside `src/`, mirroring its tree — `tests/server/orders/service.test.ts`. `src/` holds no test code and builds/packages exclude tests by default. Recommended for Python and for libraries that publish `src/`.
- Either way: unit and integration tests follow the chosen layout; e2e lives in its own top-level `e2e/` (or the repo's existing e2e folder); agent evals in `evals/`; shared test helpers in one place (`tests/helpers/` or `src/test-utils/`), never copied per folder.

## Adding tests

When adding a new feature:
- Write failing test first (TDD) if practical
- Test file: `{module}.test.ts` or `test_{module}.py`, at the repo's test location (§ Where tests live)
- At minimum: one happy-path test and one error-path test

When fixing a bug:
- Add a test that reproduces the bug before fixing
- The test must fail on the buggy code, pass after the fix

## Test coverage enforcement (mandatory on every code change)

**Rule: every implementation file that is created or modified must have a paired test file.**

| Scenario | Action |
|----------|--------|
| New component/screen/module created | Create its test file at the repo's test location immediately — use the project's test-generation skill if it has one |
| Existing file modified | Open its test file, update affected test cases to match the change |
| No test file exists for a modified file | Create it before handing off or committing |

**Skip only for**: config files, type-only files, navigation wiring, constant declarations.

**Commit gate**: if a staged implementation file has no paired test file, the commit hook warns with the missing path.

**QA gate**: before commit, run the project's gate skill — it runs the test suite for all affected workspaces and blocks on failures. In `flash-mobile-app` that is `check-mobile-gates` from the `flash-frontend-dev` plugin.

## What not to add

- Do NOT add tests for things that can't fail (trivial getters, constant returns)
- Do NOT write tests that test the mock, not the code
- Do NOT test third-party library behavior
