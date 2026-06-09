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

## Adding tests

When adding a new feature:
- Write failing test first (TDD) if practical
- Test file: `{module}.test.ts` or `test_{module}.py` alongside the module
- At minimum: one happy-path test and one error-path test

When fixing a bug:
- Add a test that reproduces the bug before fixing
- The test must fail on the buggy code, pass after the fix

## Test coverage enforcement (mandatory on every code change)

**Rule: every implementation file that is created or modified must have a paired test file.**

| Scenario | Action |
|----------|--------|
| New component/screen/module created | Create `<file>.test.ts(x)` immediately — use `/gen-tests <path>` if available |
| Existing file modified | Open its `.test.ts(x)`, update affected test cases to match the change |
| No test file exists for a modified file | Create it before handing off or committing |

**Skip only for**: config files, type-only files, navigation wiring, constant declarations.

**Commit gate**: if a staged implementation file has no paired test file, the commit hook warns with the missing path and suggests `/gen-tests`.

**QA gate**: before commit, run `/verify-feature` (or equivalent) — it runs the full test suite for all affected workspaces and blocks on failures.

## What not to add

- Do NOT add tests for things that can't fail (trivial getters, constant returns)
- Do NOT write tests that test the mock, not the code
- Do NOT test third-party library behavior
