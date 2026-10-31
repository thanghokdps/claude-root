---
name: constraints
description: Sets the repo's quality bar once, with numbers — coverage of changed lines, type and lint errors, dependency vulnerabilities, bundle or page budgets — and writes it to CONSTRAINTS.md at the repo root, each row naming the command that produces the verdict and where it runs. Use when a project has no written quality bar, when "tests pass" is the only gate, or when the user asks what the agent should be held to.
when_to_use: set a quality bar, define thresholds, "coverage phải bao nhiêu", "tiêu chuẩn chất lượng của repo", CONSTRAINTS.md, what should block a commit, the gates are only pass/fail, measure where we are and hold the line, before the first /feature on a new repo, after /project-init
effort: medium
---

# constraints — the quality bar, in numbers, in one file

**Invoke:** `/constraints`

Adapted from addyosmani/agent-skills `constraint-driven-development`. `/checkpoint` (dev, if installed) and `/verify-done` read the file and report each row; the `weakened-check` hook (dev, if installed) asks before a commit that lowers a number in it.

A gate that only says pass/fail has no bar: the agent can merge untested code and nothing is red. A number without a command is an aspiration. This skill writes both, once, where review sees them.

## Step 1 — Detect before asking

Read, never ask: stack (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`), test runner and its `test` script, linters (`eslint.config.*`, `biome.json`, `.ruff.toml`), coverage already configured (`coverageThreshold`, `fail_under`, `--cov-fail-under`), CI (`.github/workflows/`, `.gitlab-ci.yml`), today's coverage (`coverage/lcov.info` or one run of the suite), bundle size if a build exists. Report what was found in two lines.

## Step 2 — Ask up to four questions, each with a default

This is the up-front phase: ask all of them in one `AskUserQuestion` call (an unanswered one takes its default). Not in a non-interactive run (`/loop`, CI, "implement all, don't ask"): take every default, write the file, and say so.

| Q | Default |
|---|---------|
| Beyond the floor, which dimensions are enforced: changed-line coverage, dependency vulnerabilities, bundle budget, page performance, accessibility, architecture boundaries? | changed-line coverage + dependency vulnerabilities; budget/perf/a11y only when the repo serves a page |
| A red check mid-task: block or warn? | block the floor and the numbered rows; warn on "Measured" rows |
| Target numbers, or measure today and hold the line? | measure and hold (a ratchet); invented numbers get ignored |
| Slowest check tolerated before the agent hands work back? | ~90 s at task end, unlimited in CI |

## Step 3 — Write `CONSTRAINTS.md` at the repo root

```markdown
# Constraints

Last reviewed: <date> by <user>

## Floor (always enforced, no setup required)

- No new suppression (`@ts-ignore`, `eslint-disable`, `# noqa`, `# type: ignore`, `istanbul ignore`, `nosemgrep`)
- No skipped or deleted test without a reason in the commit message
- No stub left in place of an implementation (`throw new Error("Not implemented")`, empty `catch {}`)
- No secrets in source
- This file is not weakened to make a change pass

## Enforced with numbers

| Dimension | Rule | Checked by | Runs at |
|-----------|------|------------|---------|
| Types | 0 errors | `npx tsc --noEmit` | every edit |
| Lint | 0 errors | `pnpm lint` | every edit |
| Coverage | changed lines ≥ 80% | `pnpm test --coverage` + `git diff` | task end, CI |
| Dependencies | nothing at high or above | `pnpm audit --audit-level high` | CI |

## Measured, not yet enforced

| Metric | Today | Direction |
|--------|-------|-----------|
| Project coverage | 62.4% | must not fall (tolerance 0.5%) |
| Bundle (main) | 184 kB | must not grow |

## Exceptions

| ID | Rule | Path | Reason | Owner | Expires |
|----|------|------|--------|-------|---------|
```

Rules for the file:
- Every row in **Enforced with numbers** names the command that produces the verdict; a row without one goes to **Measured** instead. The command is the repo's own script (`pnpm lint`, `pytest --cov`), never a tool the repo does not have — a dimension whose tool is not installed is listed under Measured with `tool: <name> not installed` until the user installs it (name the install command once, do not run it).
- Prove each Enforced command exists before writing its row: the script name is in `package.json` `scripts` (or the `pyproject` / `Makefile` equivalent) as read this session, or the binary is on the path. A script you would have to add (`test:coverage`, a coverage flag the test runner does not have yet) is not enforced today: it goes to Measured as `script to add: <name>`, and moves up once the user has it.
- A dimension needs a running URL (page performance, accessibility): skip it for a CLI, library or API with no page, and say so.
- Numbers come with the reason (`≥ 80%: high enough to force a test, low enough to allow a config line`) in the Rule cell when it is not obvious.
- An exception expires (default 90 days) and has an owner.
- Scope the expensive checks to the diff (coverage of changed lines, not of the project), and place each row at the cheapest stage that catches it: `every edit` under 5 s, `task end` under 90 s, `CI` the rest. A check that stalls the agent gets switched off, which is worse than no check.
- At least one row should be external to the agent's own tests (a vulnerability database, a linter config a person owns): a bar made only of the suite the agent writes is circular.

Then add one line to `CLAUDE.md`: `Read CONSTRAINTS.md before writing code; do not weaken it to make a change pass.`

## Step 4 — Report

Two lines: which rows are enforced with a command today, and which are measured only (and what installing would move them up). Then the standard **Decided for you** list for every default taken.

**Done when:** `CONSTRAINTS.md` exists at the root with at least the Floor and one numbered row whose command exits 0 when run now, and `CLAUDE.md` points at it.
