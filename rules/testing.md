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

## What not to add

- Do NOT add tests for things that can't fail (trivial getters, constant returns)
- Do NOT write tests that test the mock, not the code
- Do NOT test third-party library behavior
