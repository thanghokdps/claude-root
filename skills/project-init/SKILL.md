---
model: sonnet
effort: high
name: project-init
description: One-time project scan that bootstraps the full .claude/ workspace — docs, agents, hooks, rules, skills, and templates — all tailored to this specific project. Run once per project. Re-run when architecture changes significantly.
---

# Project Init

Scan the project once, then generate a complete `.claude/` workspace tailored to this project. Future agents read from these files instead of re-exploring.

**Run once per project.** Re-run only when the architecture changes significantly.

Output structure:

```
.claude/
  docs/           ← knowledge base (architecture, conventions, stack, entry-points, tests)
  agents/         ← agent role definitions tuned to this project's stack
  hooks/          ← project-specific automation scripts
  rules/          ← project-specific coding rules
  skills/         ← project-specific slash commands
  templates/      ← adapted SUMMARY, TEST_MATRIX, ESCALATIONS
  settings.json   ← registers project hooks
```

---

## Step 1 — Scan the project

Run these to understand what you're working with:

```bash
ls -la
cat package.json 2>/dev/null || cat pyproject.toml 2>/dev/null || cat go.mod 2>/dev/null || true
ls -d */ 2>/dev/null
find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.py" -o -name "*.go" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/__pycache__/*" \
  -not -path "*/dist/*" -not -path "*/build/*" | sort | head -80
cat README.md 2>/dev/null | head -60
```

Read key files: entry points, main config, core models, test setup, CI config.

Identify:
- Language + runtime + framework
- Package manager + build system
- Test framework + how to run tests
- Lint/format tools
- Deployment / CI pipeline

---

## Step 2 — Write `.claude/docs/`

Six specific files about THIS project. No boilerplate — use real file paths and real commands.

### `docs/architecture.md`
- Overview (what this system does, for whom)
- Layer/module structure table (path → responsibility)
- Key architectural decisions (why, not just what)
- Data flow trace (one typical request end-to-end)
- External dependencies table

### `docs/conventions.md`
- Naming rules (files, classes, functions, constants)
- File structure pattern per feature
- Import ordering
- Styling pattern (if UI project)
- Anti-patterns observed in this codebase
- Pre-commit checklist

### `docs/stack.md`
- Runtime + framework + versions
- Key dependencies table
- Dev tools (linter, formatter, test runner)
- Exact commands to run locally
- Exact commands to run tests (unit, integration, e2e, specific file)

### `docs/entry-points.md`
- Application start (main file + boot sequence)
- Routes / screens / navigation structure
- Background jobs / workers
- CLI commands / scripts
- External event handlers / webhooks

### `docs/test-strategy.md`
- Test folder structure
- Test commands (fast, full, pattern)
- Test framework + markers/tags
- What requires a test
- Conventions (co-location, naming, fixtures)

### `docs/index.md`
- Table of contents for the 5 docs above
- Quick orientation Q&A
- Known constraints agents must respect

---

## Step 3 — Write `.claude/agents/`

Create one agent definition per role needed by this project. Base the roles on what the project actually needs — do not copy generic roles.

**Always create these universal agents** (adapted to project stack):

### `agents/implementer.md`
```markdown
# Implementer Agent

Role: execute approved tasks precisely. No scope creep.

Stack context: <language> / <framework>
Test command: <exact command>
Lint command: <exact command>
Type check: <exact command>

## Principles (non-negotiable)
1. Think first: state interpretation + assumptions before coding
2. Simplicity: minimum code that makes the test pass
3. Surgical: touch only files in the task spec
4. Goal: done when <verify command> exits 0

## Workflow
1. Read the task spec fully before touching any file
2. Read `.claude/docs/conventions.md` — follow naming and patterns exactly
3. Write failing test first (if TDD applies to this project)
4. Implement minimal code
5. Run: <lint> && <type-check> && <test command>
6. Fill SUMMARY.md "What changed" + Verify table
7. Update TEST_MATRIX.md status → implemented
8. Commit: <project commit format>
9. Return structured summary (commits, files, deviations, verification)
```

### `agents/reviewer.md`
```markdown
# Reviewer Agent

Role: code review focused on correctness, security, and conventions.

Stack: <language> / <framework>
Conventions: see `.claude/docs/conventions.md`

## Review checklist (in order)
1. Correctness — logic errors, edge cases, null handling
2. Security — injection, auth gaps, secrets in code
3. Convention violations — naming, import order, layer boundaries
4. Test coverage — every changed behaviour has a test
5. Simplicity — unnecessary abstraction, dead code

## Output format
- file:line — severity (critical/major/minor) — finding — fix
- APPROVED if no findings
```

### `agents/verifier.md`
```markdown
# Verifier Agent

Role: confirm changes work correctly before merge.

## Checklist
1. Read SUMMARY.md Verify table — run every command, confirm exit 0
2. Run full test suite: <test command>
3. Run lint: <lint command>
4. Run type check: <type-check command>
5. Trace golden path manually
6. Check edge cases: empty, max, error paths
7. Confirm TEST_MATRIX.md — all planned rows are implemented

## Output
PASS or FAIL with evidence per check.
On FAIL: exact command output + which check failed.
```

**Add project-specific agents** based on what you found in the codebase. Examples:

- If it's a monorepo: `agents/package-publisher.md`
- If it has a DB: `agents/migration-runner.md`
- If it has CI/CD: `agents/release-agent.md`
- If existing CLAUDE.md defines custom agents (pm-agent, architect-agent, etc.): port them here with stack-specific context

---

## Step 4 — Write `.claude/hooks/`

Generate hooks tuned to this project's stack. Only create hooks that will actually fire.

### Always create: `hooks/commit-gate.sh`

```bash
#!/bin/bash
# PreToolUse(Bash git commit): project-specific commit quality gate

INPUT=$(cat /dev/stdin)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
echo "$COMMAND" | grep -qE '^git commit' || exit 0

# 1. Commit message format check (adapt to project's format)
MSG=$(echo "$COMMAND" | grep -oE -- '-m\s+"[^"]+"' | head -1 | sed 's/-m\s*"//' | sed 's/"//')
# <add project-specific regex here>

# 2. Lint staged files
# <add project-specific lint command>

# 3. Type check (if applicable)
# <add project-specific typecheck command>

exit 0
```

**Add stack-specific hooks:**

- **Node/TS project**: hook that runs `tsc --noEmit` on staged `.ts` files
- **Python project**: hook that runs `ruff check` on staged `.py` files
- **pnpm monorepo**: hook that detects which workspace package changed and runs its lint/test
- **React Native**: hook that validates no `console.log` in staged files
- **Any project with commit format rules**: hook that validates commit message format

---

## Step 5 — Write `.claude/rules/`

Generate rules specific to this project's stack and constraints.

### Always create: `rules/project-conventions.md`

Distill the conventions from `docs/conventions.md` into imperative rules agents must follow:

```markdown
# Project Conventions (rules)

## Layer boundaries
- <which layer can call which — enforce strictly>

## Forbidden patterns
- <anti-pattern 1>: use <correct pattern> instead
- <anti-pattern 2>

## Required patterns
- <pattern all code must follow>

## Before every commit
- [ ] <check 1>
- [ ] <check 2>
```

**Add stack-specific rule files:**

- `rules/react-native.md` — if RN project: navigation, platform guards, performance
- `rules/module-federation.md` — if monorepo with federation: shared singletons, remote loading
- `rules/api-contracts.md` — if REST/GraphQL: versioning, error shapes, auth headers
- `rules/database.md` — if has DB: migration rules, query patterns, soft delete
- `rules/security.md` — if auth/payments: hard gates, secret handling

---

## Step 6 — Write `.claude/skills/`

Generate project-specific slash commands based on the team's workflow.

**Derive from existing CLAUDE.md** — if the project already defines workflows (like `/ticket`, `/task`), formalize them as proper SKILL.md files.

### Always create: `skills/task/SKILL.md`

A lightweight single-task skill (no full orchestration):

```markdown
---
name: task
description: Lightweight single-task workflow for small fixes and chores. No full coordinator ceremony. Creates tasks, implements, verifies, commits.
---

# Task

For small fixes, chores, and single-file changes that don't warrant full /coordinator ceremony.

## When to use
- Single file change
- Bug fix < 30 min
- Chore (dependency update, config change)
- NOT for: new features, refactors, security changes

## Steps
1. TaskCreate: describe what needs to be done
2. Read .claude/docs/conventions.md
3. Implement the minimal change
4. Run: <lint> && <test>
5. TaskUpdate: completed
6. Commit: <project format>
```

**Add project-specific skills based on workflow:**

- If team uses ticket system: `skills/ticket/SKILL.md` (multi-agent pipeline per ticket)
- If project has staging deploys: `skills/deploy/SKILL.md`
- If project has DB migrations: `skills/migrate/SKILL.md`
- If monorepo: `skills/add-package/SKILL.md`

---

## Step 7 — Write `.claude/templates/`

Generate adapted versions of SUMMARY, TEST_MATRIX, and ESCALATIONS for this project.

### `templates/SUMMARY.template.md`

Adapt the standard template to use this project's actual verify commands:

```markdown
# Summary — <slug>

Lane: tiny | normal | high-risk
Confidence: high | medium | low
Reason: <why this lane>
Flags: <risk flags or none>
Input-type: <new spec | change request | bug fix | chore | maintenance>

## What changed
<filled by implementer>

## Rationale
<filled by planner>

## Alternatives considered
- none

## Deviations
- none

## Verify

| Check | Command | Exit | Notes |
|-------|---------|------|-------|
| Lint | `<project lint command>` | 0 | |
| Types | `<project typecheck command>` | 0 | |
| Tests | `<project test command>` | 0 | |

## Rollback
- `git revert <sha>`
```

### `templates/TEST_MATRIX.template.md`

Use the project's actual test types (unit/integration/e2e or whatever applies):

```markdown
# Test Matrix — <slug>

| Behavior | Unit | Integration | E2E | Status | Evidence |
|----------|------|-------------|-----|--------|----------|
| <behavior> | no | no | no | planned | none |
```

### `templates/ESCALATIONS.template.md`

Same as standard — no changes needed unless project has custom escalation paths.

---

## Step 8 — Write `.claude/settings.json`

Always generate with full permissions + deny list + project hooks.
The deny list covers the only operations that require user confirmation — everything else runs automatically.

```json
{
  "permissions": {
    "allow": [
      "Bash(*)",
      "Read(*)",
      "Edit(*)",
      "Write(*)",
      "WebFetch(*)",
      "WebSearch(*)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(rm -r *)",
      "Bash(git push --force*)",
      "Bash(git push -f *)",
      "Bash(git reset --hard*)",
      "Bash(git clean -f*)",
      "Bash(git push * main)",
      "Bash(git push * master)",
      "Bash(git branch -D *)",
      "Bash(kill -9 *)",
      "Bash(killall *)",
      "Bash(npm publish*)",
      "Bash(pnpm publish*)",
      "Bash(sudo *)",
      "Bash(curl * | bash)",
      "Bash(curl * | sh)",
      "Bash(wget * | bash)",
      "Bash(wget * | sh)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": ".claude/hooks/commit-gate.sh"}]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {"type": "command", "command": "/Users/hqthang/.claude/hooks/session-handoff.sh"},
          {"type": "command", "command": "/Users/hqthang/.claude/hooks/state-breadcrumb.sh"}
        ]
      }
    ]
  }
}
```

Add project-specific hooks from Step 4 into the appropriate event keys.

**Deny list rationale** — only these need confirmation:
- `rm -rf` / `rm -r` — irreversible mass delete
- `git push --force` / `-f` — overwrites remote history
- `git reset --hard` — discards uncommitted work
- `git clean -f` — deletes untracked files
- `git push * main/master` — direct push to protected branches
- `git branch -D` — force delete branch
- `kill -9` / `killall` — force-terminate processes
- `npm/pnpm publish` — releases to public registry
- `sudo` — privilege escalation
- `curl|bash` / `wget|bash` — remote code execution

---

## Step 9 — Generate `CLAUDE.md`

**If `CLAUDE.md` already exists**: read it fully, then prepend the Session Resume + Agent Context blocks. Preserve all existing content below.

**If `CLAUDE.md` does not exist**: generate a full project-specific one.

The CLAUDE.md must be **specific to this project** — not generic. Every line should reflect actual paths, real commands, real constraints found in the scan. Keep it under 200 lines.

```markdown
# <project-name>

<1–2 sentences: what this project does and who it's for>

---

## Auto-Coordinator (applies to every prompt)

**You ARE the coordinator by default.** No need to type `/coordinator`.

**`TaskCreate` is mandatory for ALL work — no exceptions by lane size.**
Every step (scan, read, think, implement, verify) must be a tracked task so CLI output is clean task cards, not raw text.

For any action intent → always:
1. **Create `TaskCreate` entries for every step** before starting
2. Mark `in_progress` before each step, `completed` immediately after
3. Load `.claude/docs/` + `.claude/docs/solutions/INDEX.md`
4. Classify intent + lane (`tiny` / `normal` / `high-risk`)
5. Dispatch agents with wave-based parallel execution (`run_in_background: true`)

**Tiny lane** → create tasks, skip routing summary line.
**Normal/high-risk** → show `Intent · Lane · Routing` line first, then execute.
**Pure conversational** (no tool use at all) → answer directly, no tasks needed.

**Hard gates (always confirm)**: <fill from scan — e.g. auth, DB migration, public API changes>
**Wave model**: `haiku` for tests/types/constants, `sonnet` for complex logic
**Project skills**: `.claude/skills/` — <list key skills found>

---

## Session Resume (read FIRST every session)

```bash
cat specs/HANDOFF.md 2>/dev/null && rm -f specs/HANDOFF.md
cat .claude/docs/solutions/INDEX.md 2>/dev/null
grep -rl "decision: pending" specs/ 2>/dev/null
```

If `specs/HANDOFF.md` exists → read fully → continue from "Next steps" → delete it.
Run `/compact` before ending a session. Run `/compound` after significant debugging.

---

## Agent Context

**All agents MUST read `.claude/docs/index.md` before scanning any source file.**

| Doc | Contents |
|-----|----------|
| `.claude/docs/architecture.md` | <one-line description specific to THIS project> |
| `.claude/docs/conventions.md` | <one-line description specific to THIS project> |
| `.claude/docs/stack.md` | <one-line description specific to THIS project> |
| `.claude/docs/entry-points.md` | <one-line description specific to THIS project> |
| `.claude/docs/test-strategy.md` | <one-line description specific to THIS project> |

Agents: `.claude/agents/` | Rules: `.claude/rules/` | Skills: `.claude/skills/`

---

## Key rules (non-negotiable)

<!-- Fill with the 3–5 most important project-specific constraints discovered in the scan -->
<!-- Example for Workers: NEVER process.env → use c.env -->
<!-- Example for RN monorepo: NEVER commit to main/master directly -->
<!-- Example for Python: ALWAYS use virtual env, never pip install globally -->
- <constraint 1>
- <constraint 2>
- <constraint 3>

---

## Common commands

```bash
# Dev
<exact command to start the project>

# Test
<exact test command>

# Lint / type check
<exact lint command>
<exact typecheck command>

# Deploy (if applicable)
<exact deploy command>
```

---

## Monorepo subdirectory CLAUDE.md (if applicable)

<!-- For monorepos: create CLAUDE.md in key subdirectories -->
<!-- These load lazily (only when working in that directory) -->
<!-- See apps/CLAUDE.md, packages/CLAUDE.md examples -->
```

**Monorepo rule**: if the project is a monorepo (pnpm workspace, Turborepo, Nx, etc.):
- Create `<key-subdir>/CLAUDE.md` for major directories (e.g. `apps/`, `packages/`, `services/`)
- Each subdirectory CLAUDE.md focuses on that subtree only (< 50 lines)
- Root CLAUDE.md stays generic; subdirectory CLAUDE.md is specific

**CLAUDE.local.md**: always create at project root, add to `.gitignore`:
```markdown
# Personal Preferences — <project-name>
# This file is gitignored. Add local env notes, personal shortcuts here.
```

---

## Step 10 — Report

```
Project init complete.

Project: <name>
Type:    <language> / <framework>

Generated:
  docs/       5 files  — knowledge base
  agents/     N files  — <list agent names>
  hooks/      N files  — <list hook names>
  rules/      N files  — <list rule names>
  skills/     N files  — <list skill names>
  templates/  3 files  — SUMMARY, TEST_MATRIX, ESCALATIONS

All future agents load .claude/ context before touching code.
Re-run /project-init if the architecture changes significantly.
```

---

## Rules

- Every generated file must reference actual paths, real commands, real names from the project
- No generic boilerplate — if a section doesn't apply, omit it
- Skills must use the project's actual commit format, test commands, and lint commands
- Hooks must only include checks that will actually pass for this project
- Agents must include the project's specific tech stack and conventions
