---
model: opus
effort: high
name: project-init
description: One-time project scan that bootstraps the full .claude/ workspace — docs, agents, hooks, rules, skills, templates, memory, and CLAUDE.md — all tailored to this specific project. Run once per project. Re-run when architecture changes significantly.
---

# Project Init

Bootstrap a complete `.claude/` workspace for the current project.

**Run once per project.** Re-run only when the architecture changes significantly.

Final output:
```
.claude/
  docs/           ← 6 knowledge-base files (written by Claude)
  agents/         ← role definitions adapted to this project's stack
  rules/          ← universal + stack-specific + project conventions
  skills/         ← universal + project-specific slash commands
  hooks/          ← automation scripts registered in settings.json
  templates/      ← SUMMARY, TEST_MATRIX, ESCALATIONS with real commands
  memory/         ← bootstrapped (MEMORY.md, project/context.md, user.md)
  settings.json   ← hooks wired, permissions set
CLAUDE.md         ← project-specific coordinator config
```

---

## Step 1 — Run init.sh (automation layer)

Locate and run the harness bootstrap script. It handles everything that can be automated without reading code.

```bash
INIT_SCRIPT=$(find ~ -name "init.sh" -path "*/Claude/scripts/*" 2>/dev/null | head -1)
echo "Found: $INIT_SCRIPT"
bash "$INIT_SCRIPT" "$(pwd)"
```

`init.sh` will:
- Detect tech stack (Node/TS/Python/Go/Rust/Java + frameworks/libs)
- Copy universal rules: `git.md`, `testing.md`, `orchestration.md`, `memory.md`
- Copy stack-specific rules: `typescript.md`, `python.md`, `react.md`, `nextjs.md`, etc.
- Copy universal skills: `feature`, `fix-bug`, `code-review`, `checkpoint`, `sync-memory`
- Copy all agents: `implementer`, `reviewer`, `verifier`, `pm-agent`, `architect`, `qa`, `auto-dev`
- Copy all templates: `SUMMARY`, `TEST_MATRIX`, `ESCALATIONS`, `AGENT_WATCHER`
- Copy hooks: `commit-quality-gate`, `branch-guard`, `scope-gate`, `save-commit-memory`, `state-breadcrumb`
- Write `.claude/settings.json` with all hooks registered
- Bootstrap `.claude/memory/` (MEMORY.md, project/context.md, user.md)
- Write a base `CLAUDE.md` with real commands extracted from `package.json` / manifests

---

## Step 2 — Scan the project (intelligence layer)

Use `init.sh` output (detected signals) as a starting point, then read key files to understand the codebase deeply enough to write tailored docs, rules, skills, and agents.

```bash
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.py" -o -name "*.go" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/__pycache__/*" \
  -not -path "*/dist/*" -not -path "*/build/*" | sort | head -80
cat README.md 2>/dev/null | head -60
```

Read: entry points, main config, core models, test setup, CI config.

Identify and note:
- Language + framework + versions
- Package manager + build system
- Test framework + exact commands
- Lint/type-check commands
- Architecture pattern (monorepo, layered, modular, event-driven, etc.)
- Key directories and their responsibilities
- Any existing conventions or anti-patterns

---

## Step 3 — Write `.claude/docs/` (6 files)

All 6 files must use real file paths, real commands, real names — no boilerplate.

### `docs/architecture.md`
- What this system does, for whom
- Module/layer table: `| path | responsibility |`
- Key architectural decisions (why, not just what)
- One typical request traced end-to-end
- External dependencies table

### `docs/conventions.md`
- Naming rules (files, classes, functions, constants)
- File structure pattern per feature
- Import ordering rules
- Anti-patterns observed in this codebase
- Pre-commit checklist

### `docs/stack.md`
- Runtime + framework + exact versions
- Key dependencies table
- Dev tools (linter, formatter, test runner, type checker)
- Exact commands: dev server, test (unit / integration / single file), lint, type-check, build, deploy

### `docs/entry-points.md`
- Application start (main file + boot sequence)
- Routes / screens / navigation structure
- Background jobs / workers / cron
- CLI commands / scripts
- External event handlers / webhooks

### `docs/test-strategy.md`
- Test folder structure
- Test commands (fast subset, full suite, pattern filter)
- Test framework + markers/tags
- What requires a test (and what doesn't)
- Conventions: co-location, naming, fixtures, mocking policy

### `docs/index.md`
- Table of contents linking the 5 docs above
- Quick orientation Q&A (3–5 questions a new agent would ask)
- Known constraints agents must respect (e.g. "never raw SQL", "use pnpm only")

---

## Step 4 — Adapt `.claude/agents/` with project stack

`init.sh` copied generic agent templates. Now fill in project-specific values in each agent file.

For each agent in `.claude/agents/`:
- Replace placeholder stack info with actual: language, framework, test command, lint command, type-check command
- Replace placeholder commit format with this project's actual format (from `docs/conventions.md`)
- Add project-specific constraints from `docs/index.md`

Key agents to adapt:

**`agents/implementer.md`** — fill in:
```
Stack: <language> / <framework>
Test:  <exact test command>
Lint:  <exact lint command>
Types: <exact typecheck command>
Commit format: <type>: <description>
```

**`agents/reviewer.md`** — fill in:
```
Stack: <language> / <framework>
Conventions: see .claude/docs/conventions.md
Key anti-patterns: <from docs/conventions.md>
```

**`agents/verifier.md`** — fill in:
```
Full test suite: <exact command>
Lint: <exact command>
Type check: <exact command>
```

**`agents/qa.md`**, **`agents/architect.md`**, **`agents/pm-agent.md`** — add project context (stack, key dirs, entry points).

Add project-specific agents if warranted:
- Monorepo → `agents/package-publisher.md`
- Database → `agents/migration-runner.md`
- CI/CD pipeline → `agents/release-agent.md`

---

## Step 5 — Adapt `.claude/templates/` with real commands

`init.sh` copied generic templates. Replace placeholder commands with project-specific ones.

**`templates/SUMMARY.template.md`** — update the Verify table:
```markdown
| Check | Command | Exit |
|-------|---------|------|
| Lint  | `<real lint command>`       | 0 |
| Types | `<real typecheck command>`  | 0 |
| Tests | `<real test command>`       | 0 |
```

**`templates/TEST_MATRIX.template.md`** — update column headers to match what test types this project actually has (unit / integration / e2e / eval — only the ones that exist).

**`templates/ESCALATIONS.template.md`** — add project-specific hard-gate conditions discovered in the scan (e.g. "DB migration", "auth changes", "public API contract").

---

## Step 6 — Write project-specific `.claude/rules/`

`init.sh` already copied universal and stack-specific rules. Now add a project-conventions rule file.

### `rules/project-conventions.md`

Distill this project's actual conventions into imperative rules:

```markdown
# Project Conventions

## Layer boundaries
- <which layer calls which — enforce strictly>

## Forbidden patterns
- <anti-pattern>: use <correct pattern> instead

## Required patterns
- <pattern all code must follow>

## Before every commit
- [ ] <check 1>
- [ ] <check 2>
```

Add additional rule files only if a domain genuinely needs its own rules (e.g. `rules/api-contracts.md` if the project has a versioned public API, `rules/database.md` if it has complex migration patterns).

---

## Step 7 — Write project-specific `.claude/skills/`

`init.sh` copied universal skills. Add project-specific slash commands based on workflow patterns found in the scan.

### Always create: `skills/task/SKILL.md`

Lightweight single-task skill (no full coordinator ceremony):

```markdown
---
name: task
description: Lightweight single-task workflow for small fixes and chores.
---

# Task

For small fixes, chores, single-file changes.

## Steps
1. TaskCreate: describe what needs to be done
2. Read .claude/docs/conventions.md
3. Implement the minimal change
4. Run: <lint> && <typecheck> && <test>
5. TaskUpdate: completed
6. Commit: <project format>
```

Add more skills if the project's workflow warrants it:
- Team uses ticket system → `skills/ticket/SKILL.md` (full multi-agent pipeline per ticket)
- Has staging deploys → `skills/deploy/SKILL.md`
- Has DB migrations → `skills/migrate/SKILL.md`
- Is a monorepo → `skills/add-package/SKILL.md`

---

## Step 8 — Finalize `CLAUDE.md`

`init.sh` wrote a base `CLAUDE.md`. Now make it project-specific.

**If the Agent Context block is missing**, add it:

```markdown
## Agent Context

**All agents MUST read `.claude/docs/index.md` before scanning any source file.**

| Doc | Contents |
|-----|----------|
| `.claude/docs/architecture.md`  | <one-line specific to THIS project> |
| `.claude/docs/conventions.md`   | <one-line specific to THIS project> |
| `.claude/docs/stack.md`         | <one-line specific to THIS project> |
| `.claude/docs/entry-points.md`  | <one-line specific to THIS project> |
| `.claude/docs/test-strategy.md` | <one-line specific to THIS project> |
```

**Update the Key Rules section** with 3–5 constraints from `docs/index.md`.

**Update Common Commands** to match exactly what was found in `docs/stack.md`.

**Keep it under 200 lines** — if longer, extract to `.claude/docs/`.

---

## Step 9 — Report

```
Project init complete.

Project: <name>
Stack:   <detected signals>

Generated by init.sh (automation):
  rules/       N files  — universal + stack-specific
  agents/      N agents — implementer, reviewer, verifier, pm, architect, qa, auto-dev
  skills/      N skills — feature, fix-bug, code-review, checkpoint, sync-memory
  hooks/       N files  — commit-gate, branch-guard, scope-gate, save-commit-memory
  templates/   N files  — SUMMARY, TEST_MATRIX, ESCALATIONS, AGENT_WATCHER
  memory/      bootstrapped (MEMORY.md, project/context.md, user.md)
  settings.json hooks registered

Written/adapted by Claude (intelligence):
  docs/        6 files  — architecture, conventions, stack, entry-points, test-strategy, index
  agents/      adapted  — stack commands filled in, project constraints added
  templates/   adapted  — real verify commands inserted
  rules/       + project-conventions.md
  skills/      + task/SKILL.md (+ project-specific if applicable)
  CLAUDE.md    finalized with Agent Context + real constraints

All future agents load .claude/docs/ before touching code.
Re-run /project-init if the architecture changes significantly.
```
