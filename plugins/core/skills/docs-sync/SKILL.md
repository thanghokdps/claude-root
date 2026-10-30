---
effort: medium
name: docs-sync
description: Brings the project's knowledge base (.claude/docs/ and CLAUDE.md) up to date with a branch's diff — maps each change to the doc it makes stale (new route, job, layer, command, dependency, convention, test layout), edits only those sections with real paths, and commits them with the code. Use at the end of a feature, scaffold or fix, before the PR, so the next session reads current docs instead of rescanning the code.
when_to_use: a feature or scaffold is done and about to land, "update the docs", "cập nhật docs", ".claude/docs bị cũ", docs are stale, CLAUDE.md is out of date, before /finish-branch opens a PR, a new route, table, job, command or dependency was added
---

# docs-sync — keep the knowledge base as current as the code

**Invoke:** `/docs-sync [base branch]` — default: the merge base with `origin/HEAD`.

Agents read `.claude/docs/` instead of rescanning the code, so a stale doc is worse than none: it sends them confidently to the wrong place. The docs are current when every fact this diff changed is in them, with a path that exists.

No `.claude/docs/index.md` → run `/project-init` instead and stop here; it writes the whole set from the code.

## Step 1 — Read the diff by kind

```bash
base="$(git merge-base HEAD origin/HEAD)"
git diff --stat "$base"...HEAD
git diff --name-status "$base"...HEAD
```

Uncommitted work counts too: add `git status --short`.

## Step 2 — Map each change to its doc

| The diff adds, moves or removes | Update |
|---|---|
| A route, screen, handler, job, cron, webhook, CLI command | `entry-points.md` |
| A module, layer, service boundary, external system, data flow; a key decision | `architecture.md` (and the ADR if the decision has one) |
| A dependency, runtime or tool version, a dev/test/build/deploy command, an env var | `stack.md`, and Common Commands in `CLAUDE.md` |
| A naming or file-layout pattern the change sets for later code; an anti-pattern it removed | `conventions.md` |
| A test location, fixture, marker, test command | `test-strategy.md` |
| A table, column or relation | `docs/erd.md` when the repo keeps one (`/db-change` owns it — backend, if installed) |
| A constraint every agent must respect | `index.md` constraints, and Key Rules in `CLAUDE.md` |
| A domain term | `glossary.md` via `/domain-model` (plan, if installed) |

A change that maps to no row (an internal fix, a refactor inside one file) needs no doc edit. Say so and stop.

**Done when:** every file in the diff is mapped to a doc section, or marked "no doc impact".

## Step 3 — Edit only those sections

- Read the section first, then edit it with Edit: add the new fact, fix the one it replaced, delete the one the diff removed. Never regenerate a whole doc.
- Every path, command and name you write must exist now: `ls` the path, run `--help` or a dry run for a command when cheap.
- Keep `CLAUDE.md` under 200 lines; detail goes to `.claude/docs/`, `CLAUDE.md` keeps the pointer.
- If the repo has an `AGENTS.md` that `CLAUDE.md` imports (`@AGENTS.md`), shared facts go to `AGENTS.md`; Claude-only notes stay in `CLAUDE.md`.

**Done when:** every mapped section is edited and every path it names exists.

## Step 4 — Commit with the code

```bash
git add .claude/docs/<files> CLAUDE.md AGENTS.md   # only the ones you changed
git commit -m "docs: sync .claude/docs with <what changed>"
```

On a feature branch, before the PR, so the reviewer sees code and docs together. Never commit to `main` or an environment branch.

## Output

```markdown
Docs sync — <branch>
- entry-points.md: added `POST /api/orders/:id/refund` → `src/routes/orders.ts:88`
- stack.md: `pnpm test:e2e` added
- No doc impact: src/lib/format.ts (internal refactor)
```
