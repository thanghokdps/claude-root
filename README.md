# Claude Harness — Skill & Agent Library

A portable governance framework for [Claude Code](https://claude.ai/code). It installs into `~/.claude/` and bootstraps any project with a full AI-agent workspace: skills (slash commands), rules, hooks, agent role definitions, memory, and spec templates — all tuned to the detected tech stack.

**Source library, not an app.** Changes here propagate to `~/.claude/` (global) and to individual projects via `/project-init`.

---

## Table of Contents

1. [How it works](#how-it-works)
2. [Repository structure](#repository-structure)
3. [Installation](#installation)
4. [Bootstrapping a project](#bootstrapping-a-project)
5. [Skills reference](#skills-reference)
6. [Hooks reference](#hooks-reference)
7. [Rules reference](#rules-reference)
8. [Agents reference](#agents-reference)
9. [Scripts reference](#scripts-reference)
10. [Templates reference](#templates-reference)
11. [Memory system](#memory-system)
12. [The coordinator flow](#the-coordinator-flow)
13. [Risk lanes & hard gates](#risk-lanes--hard-gates)
14. [Extending the harness](#extending-the-harness)

---

## How it works

Two layers:

| Layer | What it is | Lives in |
|-------|-----------|---------|
| **Skills** (engine) | Invocable `/skills` that do the work — feature, fix-bug, review, verify | `skills/`, `agents/` |
| **Harness** (control) | Thin governance layer that determines risk, routes work, enforces gates | `hooks/`, `rules/`, memory system |

The engine answers *"how do I build this?"* The harness answers *"how careful should I be, and who needs to approve?"*

**Core principle:** Ceremony scales with risk. Human interruption scales with ambiguity.

- **Risk** → how much proof and process (lanes: tiny / normal / high-risk)
- **Ambiguity** → whether a human is asked (only to confirm intent, not classify risk)

### Request lifecycle

```
prompt
  → scope-gate.sh          (classify risk, warn on stale memory)
  → /coordinator            (route to the right agent sequence)
  → Explorer / Planner      (understand + plan)
  → Implementer / Debugger  (build)
  → Verifier / Reviewer     (prove)
  → commit-quality-gate.sh  (block bad commits)
  → save-commit-memory.sh   (persist to memory)
  → session-handoff.sh      (write HANDOFF.md on session end)
```

---

## Repository structure

```
Downloads/Claude/                    ← this repo (the source library)
├── CLAUDE.md                        ← project instructions for Claude Code
├── HARNESS.md                       ← philosophy / architecture reference
├── README.md                        ← this file
│
├── agents/                          ← sub-agent role definitions
│   ├── architect.md
│   ├── qa.md
│   └── reviewer.md
│
├── hooks/                           ← bash automation scripts
│   ├── blast-radius-check.sh        ← warn when editing files outside plan scope
│   ├── branch-guard.sh              ← block force-push to protected branches
│   ├── commit-quality-gate.sh       ← block secrets / debug artifacts in commits
│   ├── headroom-compress.sh         ← auto-trigger context compression on large outputs
│   ├── risk-corroboration.sh        ← block commits when diff risk > declared lane
│   ├── save-commit-memory.sh        ← auto-save commit info to memory after commit
│   ├── scope-gate.sh                ← inject coordinator context on every prompt
│   ├── session-handoff.sh           ← write HANDOFF.md on session end
│   ├── state-breadcrumb.sh          ← append session breadcrumb to memory
│   └── stacks/
│       ├── eslint-on-edit.sh        ← run eslint --fix after editing TS/JS files
│       └── ruff-on-edit.sh          ← run ruff fix after editing Python files
│
├── memory/                          ← memory templates
│   ├── MEMORY.md.template           ← index file template
│   └── templates/
│       ├── feedback.md              ← feedback memory entry template
│       ├── project.md               ← project context memory template
│       └── user.md                  ← user profile memory template
│
├── rules/                           ← universal rules injected into all agents
│   ├── agent-principles.md          ← Karpathy's 4 principles (hard rules)
│   ├── auto-correct-scope.md        ← when to auto-fix vs ask human
│   ├── behavior.md                  ← 5 core agent behaviors
│   ├── code-quality.md              ← readability, DRY, guard clauses
│   ├── git-workflow.md              ← commit format, branches, staging
│   ├── git.md                       ← condensed git rules
│   ├── memory.md                    ← how to read and write memory
│   ├── orchestration.md             ← risk lanes, sub-agent rules
│   ├── plan-format.md               ← PLAN.md XML task format
│   ├── security.md                  ← secrets, auth/authz, input validation
│   ├── testing.md                   ← Arrange→Act→Assert, coverage, mocking
│   ├── typescript.md                ← TypeScript strict mode, types, async
│   ├── wave-parallelism.md          ← wave-based parallel agent execution
│   └── stacks/
│       ├── fastapi.md               ← FastAPI-specific rules
│       ├── langgraph.md             ← LangGraph-specific rules
│       ├── nextjs.md                ← Next.js-specific rules
│       ├── python.md                ← Python-specific rules
│       └── typescript.md            ← TypeScript-specific rules
│
├── scripts/                         ← install / bootstrap scripts
│   ├── init.sh                      ← main bootstrap script
│   ├── save-session-memory.sh       ← manually save session context
│   ├── setup-headroom.sh            ← install headroom context compression
│   └── sync-team.sh                 ← team sync: pull + rebuild memory
│
├── skills/                          ← slash command definitions
│   ├── README.md
│   ├── brainstorming/SKILL.md       ← /brainstorming
│   ├── btw/SKILL.md                 ← /btw
│   ├── checkpoint/SKILL.md          ← /checkpoint
│   ├── code-review/SKILL.md         ← /code-review
│   ├── compact/SKILL.md             ← /compact
│   ├── compound/SKILL.md            ← /compound
│   ├── coordinator/SKILL.md         ← /coordinator (main orchestration hub)
│   ├── create-pr/SKILL.md           ← /create-pr
│   ├── feature/SKILL.md             ← /feature
│   ├── figma-to-screen/SKILL.md     ← /figma-to-screen
│   ├── fix-bug/SKILL.md             ← /fix-bug
│   ├── gen-tests/SKILL.md           ← /gen-tests
│   ├── init-project/SKILL.md        ← /init-project (legacy alias)
│   ├── project-init/SKILL.md        ← /project-init
│   ├── review-diff/SKILL.md         ← /review-diff
│   ├── sync-memory/SKILL.md         ← /sync-memory
│   ├── verify-feature/SKILL.md      ← /verify-feature
│   └── writing-plans/SKILL.md       ← /writing-plans
│
└── templates/                       ← artifact templates copied into each project
    ├── CLAUDE.md.template
    ├── ESCALATIONS.template.md
    ├── SUMMARY.template.md
    ├── TEST_MATRIX.template.md
    └── settings.json.template
```

---

## Installation

### One-time global install

```bash
cp -r ~/Downloads/Claude ~/.claude-harness
chmod +x ~/.claude-harness/scripts/*.sh
chmod +x ~/.claude-harness/hooks/*.sh
```

This makes the harness available system-wide. Skills and rules are installed into individual projects via `init.sh` (see below).

### Optional: context compression (headroom)

Headroom automatically compresses large tool outputs to reduce token usage.

**Requires:** Python 3.12 (`brew install python@3.12`) and the `claude` CLI.

```bash
bash ~/.claude-harness/scripts/setup-headroom.sh
```

What it does:
1. Creates a virtualenv at `~/.headroom-env`
2. Installs `headroom-ai[all,mcp]`
3. Registers the headroom MCP server (`headroom_compress`, `headroom_retrieve`, `headroom_stats`)

After setup, the `headroom-compress.sh` hook auto-triggers compression whenever a tool output exceeds ~8 KB.

---

## Bootstrapping a project

Run once per project to generate a tailored `.claude/` workspace.

### Option A — Claude Code (recommended)

```bash
cd my-project
cp ~/.claude-harness/CLAUDE_LEGACY.md ./CLAUDE.md
# Open Claude Code, then type:
/project-init
```

The `/project-init` skill scans the codebase, then writes every file in `.claude/` — docs, agents, hooks, rules, skills, templates, and `settings.json` — using real paths and real commands from the project.

### Option B — Shell script

```bash
cd my-project
~/.claude-harness/scripts/init.sh
# OR target a specific path:
~/.claude-harness/scripts/init.sh /path/to/my-project
```

### What `init.sh` detects

The script scans manifests and `src/` for signals:

| Signal | Detection trigger |
|--------|------------------|
| `nodejs` | `package.json` exists |
| `typescript` | `tsconfig.json` or `"typescript"` in package.json |
| `nextjs` | `"next"` in package.json |
| `python` | `requirements.txt`, `pyproject.toml`, or `setup.py` |
| `fastapi` | `fastapi` in requirements/pyproject |
| `langgraph` | `langgraph` in requirements or package.json |
| `golang` | `go.mod` |
| `java` | `pom.xml` or `build.gradle` |
| `rust` | `Cargo.toml` |
| `docker` | `Dockerfile` or `docker-compose.yml` |
| `prisma` | `"prisma"` in package.json or `prisma` in `src/` |
| `postgres` | `postgres` or `pg` in `src/` |
| `redis` | `redis` in `src/` |

### What gets generated

```
your-project/
├── CLAUDE.md                    ← Fill in: run commands, architecture, constraints
└── .claude/
    ├── settings.json            ← Hooks auto-registered, deny-list set
    ├── docs/                    ← Knowledge base (written by /project-init)
    │   ├── index.md
    │   ├── architecture.md
    │   ├── conventions.md
    │   ├── stack.md
    │   ├── entry-points.md
    │   └── test-strategy.md
    ├── rules/
    │   ├── git.md
    │   ├── testing.md
    │   ├── orchestration.md
    │   ├── memory.md
    │   └── <stack>.md           ← Stack-specific rules (typescript, python, etc.)
    ├── skills/
    │   ├── feature/SKILL.md
    │   ├── fix-bug/SKILL.md
    │   ├── code-review/SKILL.md
    │   ├── checkpoint/SKILL.md
    │   └── sync-memory/SKILL.md
    ├── hooks/
    │   ├── commit-quality-gate.sh
    │   ├── branch-guard.sh
    │   ├── save-commit-memory.sh
    │   ├── state-breadcrumb.sh
    │   └── scope-gate.sh
    └── memory/
        ├── MEMORY.md            ← Index (loaded every session)
        ├── user.md              ← Fill in: your role, preferences
        ├── project/
        │   └── context.md       ← Fill in: goals, decisions, deadlines
        ├── feedback/            ← Auto-saved from corrections
        ├── commits/             ← Auto-saved after each git commit
        └── sessions/            ← Auto-saved at session end
```

### After bootstrapping — fill in three files

1. **`CLAUDE.md`** — add the actual run commands, architecture summary, and constraints
2. **`.claude/memory/project/context.md`** — add project goals, active decisions, deadlines
3. **`.claude/memory/user.md`** — add your role and working preferences

---

## Skills reference

Skills are slash commands Claude runs as guided workflows. Each lives in `skills/<name>/SKILL.md`.

### `/coordinator <request>` — Main orchestration hub

**Invoke:** `/coordinator add dark mode to the settings page`

The auto-coordinator is active by default — every prompt is treated as a coordinator request. You do not need to type `/coordinator` explicitly.

**What it does:**

1. **Step 0** — Load `.claude/docs/` and `docs/solutions/INDEX.md` (do not re-scan the codebase if docs exist)
2. **Step 1** — Parse the prompt: extract intent, scope, urgency, and risk signals
3. **Step 2** — Classify into an intent category and assign a lane (tiny / normal / high-risk)
4. **Step 3** — Confidence check (1–5); if ≤ 3 on high-risk, ask before dispatching
5. **Step 4** — Initialize `specs/<slug>/` (SUMMARY.md, TEST_MATRIX.md, ESCALATIONS.md); create TaskCreate entries for every agent step
6. **Step 5** — Wave execution: dispatch all same-wave tasks in a single message with `run_in_background: true`; verify each wave before advancing
7. **Step 6** — Synthesize results; run Verifier; report PASS / FAIL

**Intent categories:**

| Category | Trigger keywords | Default agent sequence |
|---|---|---|
| `new-feature` | add, build, create, implement | Planner → Implementer → Verifier |
| `bug-fix` | fix, broken, crash, not working | Debugger → Implementer → Verifier |
| `refactor` | refactor, clean up, rename, simplify | Refactorer → Verifier |
| `code-review` | review, audit, check | Reviewer |
| `verify` | verify, confirm, does this work | Verifier |
| `explore` | where is, how does, explain, find | Explorer |
| `security` | security, vuln, injection, XSS | Security Reviewer |
| `performance` | slow, optimize, latency, memory leak | Performance Analyst |
| `docs` | document, README, docstring | Doc Writer |
| `question` | conversational, no action implied | Direct answer — no dispatch |

**Output (for normal/high-risk):**
```
Intent:    new-feature · Lane: normal · Confidence: 4/5
Routing:   Planner → Implementer → Verifier
Assumption: none
Specs dir: specs/add-dark-mode/
```

---

### `/feature <description>` — Implement a new feature

**Invoke:** `/feature add CSV export to the reports page`

**Stages:**

| Stage | What happens |
|-------|-------------|
| 0 — Risk intake | Evaluate 10-flag checklist; assign lane (tiny/normal/high-risk) |
| 1 — Research | Does this already exist? Lightest path? Blast radius? (normal+ only) |
| 2 — Plan | Step-by-step plan with exact commands; save to `specs/<slug>/PLAN.md` (high-risk only) |
| 3 — Build | Follow the plan; run quality gates after each chunk |
| 4 — Review | Self-review: security, type errors, debug artifacts; spawn reviewer sub-agent (high-risk) |
| 5 — Commit | `git add <specific files>` + commit; `save-commit-memory.sh` auto-fires |

**Escalation triggers:** confidence drops below medium, hard gate discovered mid-task, scope creep detected, conflicting teammate commit found in memory.

---

### `/fix-bug <symptom>` — Root-cause a bug and apply minimal fix

**Invoke:** `/fix-bug crash when uploading files larger than 10MB`

**Stages:**

| Stage | What happens |
|-------|-------------|
| 1 — Reproduce | Confirm the bug is real; document exact input/output |
| 2 — Root cause | Trace to origin; grep error messages, check git log; max 3 files before asking |
| 3 — Minimal fix | Smallest fix; no refactoring, no renaming, no extra error handling |
| 4 — Verify | Run failing test; re-run scenario; run full test suite; `tsc --noEmit` (TS projects) |
| 5 — Commit | `fix: <what was wrong and what fixed it>` |

**Rule:** Fix ONLY the specific bug. No cleanup, no "while I'm here" changes.

---

### `/code-review [low|medium|high]` — Review diff for bugs and cleanups

**Invoke:** `/code-review` or `/code-review high`

**Effort levels:**

| Level | Checks |
|-------|--------|
| `low` | Obvious correctness bugs, hardcoded secrets, missing boundary validation. Max 5 findings. |
| `medium` (default) | Everything in low + logic errors, duplicate code, type errors, OWASP Top 10. Max 10 findings. |
| `high` | Everything in medium + N+1 queries, misleading names, missing tests, architectural concerns. All findings. |

**Severity labels:** `🔴 MUST FIX` (correctness/security) · `🟡 SHOULD FIX` (likely problem) · `🔵 CONSIDER` (improvement)

**Output format:**
```markdown
### 🔴 MUST FIX — SQL injection in user search
**File:** `src/users/repo.ts:42`
**Issue:** User input interpolated directly into SQL string
**Fix:** Use parameterized query: db.query('SELECT * FROM users WHERE id = $1', [id])
```

---

### `/brainstorming` — Design-first session before implementation

**Invoke:** `/brainstorming add a notification system`

**Steps:** Explore context → clarify intent (one question at a time) → propose 2–3 approaches with trade-offs → design the chosen approach → review with user → write `specs/<slug>/design.md` → hand off to `/writing-plans`.

**Rule:** Do NOT write any implementation code during brainstorming.

---

### `/writing-plans` — Convert design doc to implementation plan

**Invoke:** `/writing-plans` (run after `/brainstorming`)

**Input:** `specs/<slug>/design.md` (written by `/brainstorming`)

**Output:** `specs/<slug>/PLAN.md` — wave-organized task list with XML tasks, file maps, and verifiable acceptance criteria. Each task has: `wave`, `files`, `action`, `verify` (shell command), `done` (measurable condition).

---

### `/project-init` — Bootstrap `.claude/` workspace for a new project

**Invoke:** `/project-init` (run once per project)

**Steps:**

| Step | Output |
|------|--------|
| 1 — Scan | Detect language, framework, tools, test setup, CI |
| 2 — Write `docs/` | architecture, conventions, stack, entry-points, test-strategy, index |
| 3 — Write `agents/` | implementer, reviewer, verifier (+ project-specific agents) |
| 4 — Write `hooks/` | commit-gate + stack-specific hooks (tsc, ruff, eslint) |
| 5 — Write `rules/` | project-conventions + stack-specific rules |
| 6 — Write `skills/` | task skill + project-specific skills |
| 7 — Write `templates/` | SUMMARY, TEST_MATRIX, ESCALATIONS adapted to project commands |
| 8 — Write `settings.json` | full permissions + deny list + project hooks |
| 9 — Generate `CLAUDE.md` | project-specific with real paths and commands |
| 10 — Report | Summary of what was generated |

**Rule:** All generated files use real file paths, real commands, and real names from the scan — no boilerplate.

---

### `/compact` — Persist session state before ending

**Invoke:** `/compact` (run when conversation is long or before ending a session)

**What it does:**
1. Run `headroom learn` if installed (mines failures into corrections)
2. Summarize the session (what was done, decisions, discoveries, current state, next steps)
3. Write to `specs/HANDOFF.md` (overwrite — only latest session matters)
4. Merge non-obvious learnings into `docs/solutions/`
5. Update global memory if user-level preferences were learned

**Next session:** Claude reads `specs/HANDOFF.md` automatically via CLAUDE.md, then deletes it.

---

### `/compound` — Crystallize session learnings into solutions

**Invoke:** `/compound` (run at end of any significant session)

Mines the session for mistakes found, solutions discovered, and patterns identified. Writes them to `docs/solutions/` so future agents don't repeat the same mistakes.

---

### `/sync-memory` — Team sync: pull + rebuild memory

**Invoke:** `/sync-memory` (run at start of each team session)

Delegates to `scripts/sync-team.sh`. What it does:
1. Stash uncommitted changes
2. Find your last known commit (from `memory/commits/last-sync.txt`)
3. `git fetch --all --prune` + `git pull`
4. Collect your commits since last sync → write to `memory/commits/<date>.md`
5. Collect team commits → flag files you both touched
6. Pop stash; update MEMORY.md index

---

### `/review-diff` — Visual diff review with diagrams

**Invoke:** `/review-diff`

Generates a Markdown review of the current git diff including: architecture diagram (Mermaid), component flowchart, and code walkthrough with inline diff blocks.

---

### `/create-pr` — Generate PR description

**Invoke:** `/create-pr`

Fills `PR_TEMPLATE.md` with: title, summary (why not how), tasks completed, file changes table, and notes. Does NOT push or create the PR — outputs the template for review.

---

### `/checkpoint` — Check progress + quality gates

**Invoke:** `/checkpoint`

Reads the active `PLAN.md`, checks each task's status, runs quality gate commands (lint, typecheck, tests), and reports completed vs remaining.

---

### `/btw <question>` — Quick one-off question without interrupting context

**Invoke:** `/btw what does the UserService.findById method return?`

Fast lookup that answers without creating tasks, specs, or side effects. Use mid-task to check something without breaking flow.

---

## Hooks reference

Hooks are bash scripts triggered by Claude Code events. They exit `0` to allow or `2` to block.

### `commit-quality-gate.sh`

**Trigger:** `PreToolUse(Bash)` when command matches `git commit`

**Checks:**

| Check | Pattern | Action |
|-------|---------|--------|
| OpenAI API key | `sk-[a-zA-Z0-9]{20,}` | BLOCK |
| AWS access key | `AKIA[0-9A-Z]{16}` | BLOCK |
| Hardcoded credential | `(password\|secret\|api_key)\s*=\s*"..."` | BLOCK |
| `.env` file staged | `.env`, `.env.local`, `.env.prod*` | BLOCK |
| Python debugger | `breakpoint()` or `pdb.set_trace()` | BLOCK |
| `console.log/debug` | Added lines with `console.log` or `console.debug` | WARN only |
| Large binary file | Staged file > 5 MB | BLOCK (suggest git-lfs) |

Skips test files (`*.test.*`, `*.spec.*`) and docs for credential scanning.

**On block:** exits 2 with `🚫 COMMIT BLOCKED` message listing all reasons.

---

### `branch-guard.sh`

**Trigger:** `PreToolUse(Bash)` when command matches `git push`

**Checks:**

| Check | Action |
|-------|--------|
| Force push (`-f`, `--force`, `--force-with-lease`) to `main/master/develop/dev` | BLOCK |
| Direct push to `main` or `master` | WARN + 3-second delay |
| Uncommitted local changes | WARN (changes will not be pushed) |

---

### `scope-gate.sh`

**Trigger:** `UserPromptSubmit` (every prompt)

Injects coordinator context into every implementation-intent prompt. Detects:
- Implementation words: add, implement, refactor, build, fix, change, etc.
- High-risk words: auth, login, jwt, payment, database, migration, schema, etc.

**Output:** JSON `additionalContext` block that activates the auto-coordinator with the appropriate lane hint. Non-blocking (exit 0 always).

---

### `blast-radius-check.sh`

**Trigger:** `PostToolUse(Edit|Write)`

Compares the edited file path against the `<files>` set declared in the active `specs/*/PLAN.md`. 

**If file is outside the plan's scope:**
- Default: WARN via JSON `additionalContext` ("blast-radius: edited X which is NOT in plan")
- Strict mode (`BLAST_RADIUS_STRICT=1`): BLOCK (exit 2)

Skips `specs/`, `docs/`, `*.md`, and `.claude/` files automatically.

---

### `risk-corroboration.sh`

**Trigger:** `PreToolUse(Bash)` on `git commit`

Cross-checks the staged diff against the Lane declared in `specs/*/SUMMARY.md`.

**Hard-gate categories it detects:**

| Category | Detection |
|----------|-----------|
| `high-blast` | Staged `settings.json` or any file under `hooks/` |
| `data-loss/migration` | Files under `migrations/` or `alembic/`; `DROP TABLE`, `DELETE FROM`, `TRUNCATE`, `ALTER TABLE` in code |
| `external-provider` | `requirements.txt`, `package.json`, etc. staged; Stripe, Twilio, SendGrid, boto3, webhooks in code |
| `auth` | `login`, `session`, `jwt`, `password`, `oauth`, `bcrypt` in added lines |
| `authorization` | `role`, `permission`, `is_admin`, `rbac` in added lines |
| `audit/security` | `audit_log`, `encrypt`, `decrypt`, `pii` in added lines |
| `weakening-validation` | `assert`, `validator`, `required=True`, `raise` removed |

**Decision logic:**
- Lane is `high-risk` → allow (corroborated)
- Lane is `tiny` or `normal` → BLOCK (mismatch)
- No declared Lane → WARN (run `/coordinator`)

---

### `save-commit-memory.sh`

**Trigger:** `PostToolUse(Bash)` after `git commit`

**Input:** None (reads from git directly)

**Output:** Appends to `.claude/memory/commits/<YYYY-MM-DD>.md`:
```markdown
## `abc1234` — 2026-06-15T10:30:00

**feat: add CSV export**

- Author: Thang Ho Quang
- Branch: `feat/csv-export`
- Files:
  src/reports/export.ts
  src/reports/export.test.ts
```

Also updates `MEMORY.md` index and writes `memory/commits/last-sync.txt` (used by `sync-team.sh`).

Never blocks — all errors exit 0 silently.

---

### `state-breadcrumb.sh`

**Trigger:** `SessionEnd`

**Output:** Appends to `.claude/memory/sessions/<YYYY-MM-DD>.md`:
```markdown
### 2026-06-15T22:00:00 — <session-id>

- Last commit: `abc1234: feat: add CSV export`
- Branch: `feat/csv-export`
- Turns: 42
```

Also updates `MEMORY.md` index. Never blocks.

---

### `session-handoff.sh`

**Trigger:** `Stop` (session end)

**Output:** Writes `specs/HANDOFF.md` with:
- Branch name
- Last 8 commits (one-line)
- Git state (staged, unstaged, untracked files)
- Open specs (from `specs/*/SUMMARY.md`)
- Unresolved escalations (`decision: pending` entries)
- Prompt to fill in "What to do next"
- Warning if ≥5 files changed (suggests running `/compound`)

The next session reads and deletes this file automatically.

---

### `headroom-compress.sh`

**Trigger:** `PostToolUse(Bash|Read)`

Checks the tool response length. If it exceeds `HEADROOM_WARN_THRESHOLD` (default: 8000 characters):
- Exits 2 with a system reminder asking Claude to call `headroom_compress`
- Claude then compresses the content and continues with a compact representation

If output is small: exits 0 silently (no overhead).

---

### `stacks/ruff-on-edit.sh`

**Trigger:** `PostToolUse(Edit)` on `.py` files (Python projects only)

Runs `ruff check --fix --silent` then `ruff format --silent` on the edited file. Never blocks.

---

### `stacks/eslint-on-edit.sh`

**Trigger:** `PostToolUse(Edit)` on `.ts`, `.tsx`, `.js`, `.jsx` files (TypeScript/JS projects only)

Runs `npx eslint --fix --quiet` if `.eslintrc*` or `eslint.config*` exists in the project root. Never blocks.

---

## Rules reference

Rules are Markdown files injected into agent prompts as governance constraints.

### Universal rules (copied to every project)

| File | What it governs |
|------|----------------|
| `agent-principles.md` | Four hard rules: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution |
| `behavior.md` | Five core behaviors: think, simplify, surgical, goal-driven, communicate clearly |
| `orchestration.md` | Risk lanes (tiny/normal/high-risk), sub-agent rules, context budget, stopping conditions |
| `auto-correct-scope.md` | Rules 1–4 for when to auto-fix vs. require human confirmation |
| `wave-parallelism.md` | Wave invariants, dispatch rules, abort conditions, model selection |
| `plan-format.md` | XML task format for PLAN.md; required fields; when to create a plan |
| `git-workflow.md` | Commit format, branch naming, staging rules, PR rules, hard gates |
| `git.md` | Condensed git rules (project-level copy) |
| `testing.md` | Arrange→Act→Assert, what to test, mocking rules, coverage guidance |
| `security.md` | Secrets, auth/authz, input validation, code patterns to auto-escalate |
| `code-quality.md` | Guard clauses, DRY, naming, dead code, performance basics |
| `typescript.md` | Strict mode, type safety, naming, async, error handling |
| `memory.md` | How to read/write the four memory types (user, feedback, project, reference) |

### Stack-specific rules (`rules/stacks/`)

Copied only when the corresponding signal is detected during init:

| File | Copied when |
|------|------------|
| `stacks/typescript.md` | `typescript` signal |
| `stacks/python.md` | `python` signal |
| `stacks/fastapi.md` | `fastapi` signal |
| `stacks/langgraph.md` | `langgraph` signal |
| `stacks/nextjs.md` | `nextjs` signal |

---

## Agents reference

Agent definitions live in `agents/`. Each has YAML frontmatter controlling how Claude Code spawns them.

### `agents/architect.md`

| Field | Value |
|-------|-------|
| Model | `sonnet` |
| Mode | `bypassPermissions` |
| Max turns | 50 |
| Background | yes |
| Isolation | `worktree` (independent git worktree) |

**Role:** Design system components, evaluate trade-offs, produce implementation plans.

**Spawned by:** `/feature` (high-risk lane) when a design decision needs independent evaluation.

**Input:** Project goals, constraints from CLAUDE.md, existing architecture, the specific problem.

**Output:**
```markdown
## Approach: <name>
**Why this over alternatives:** ...
### Files to create / modify
### Public contract changes
### Plan (ordered atomic steps)
### Risks + mitigations
```

**Rule:** Does NOT write implementation code — produces plans only.

---

### `agents/reviewer.md`

**Role:** Code review focused on correctness, security, and convention compliance.

**Review checklist (in order):**
1. Correctness — logic errors, edge cases, null handling
2. Security — injection, auth gaps, secrets
3. Convention violations — naming, import order, layer boundaries
4. Test coverage — every changed behavior has a test
5. Simplicity — unnecessary abstraction, dead code

**Output format:** `file:line — severity (critical/major/minor) — finding — fix`

---

### `agents/qa.md`

**Role:** Quality assurance — verifies that changes work correctly before merge.

**Checklist:**
1. Run all commands in `specs/<slug>/SUMMARY.md` Verify table → confirm exit 0
2. Run full test suite
3. Run lint and type check
4. Trace the golden path manually
5. Check edge cases (empty, max, error paths)
6. Confirm all TEST_MATRIX.md planned rows are implemented

---

## Scripts reference

### `scripts/init.sh`

**Usage:** `./init.sh [project-dir]`

Main bootstrap script. Scans `src/` and generates the full `.claude/` harness.

**Input:** Optional `project-dir` (defaults to `pwd`)

**Output:**
- `.claude/rules/` — universal + stack-specific rules
- `.claude/skills/` — feature, fix-bug, code-review, checkpoint, sync-memory
- `.claude/hooks/` — all core hooks + stack-specific hooks
- `.claude/memory/` — MEMORY.md, user.md, project/context.md
- `.claude/settings.json` — hooks registered, permissions set
- `CLAUDE.md` — project-specific (auto-generated, fill in after)

**Prints:** Detected signals, file counts per directory, next steps.

---

### `scripts/setup-headroom.sh`

**Usage:** `bash scripts/setup-headroom.sh`

**Requires:** Python 3.12, `claude` CLI

Installs headroom context compression:
1. Creates `~/.headroom-env` virtualenv
2. `pip install headroom-ai[all,mcp]`
3. Registers `headroom` MCP server at user scope

After setup, `headroom_compress`, `headroom_retrieve`, and `headroom_stats` are available as MCP tools in Claude Code.

---

### `scripts/sync-team.sh`

**Usage:** `./sync-team.sh [project-dir]`

**Input:** Optional `project-dir` (defaults to `pwd`)

**What it does:**
1. Stash uncommitted changes
2. Read `memory/commits/last-sync.txt` to find your last recorded commit
3. `git fetch --all --prune` + `git pull --rebase=false`
4. Collect your commits since last sync (by `git config user.name`)
5. For each commit: record hash, date, subject, changed files → write to `memory/commits/<date>.md`
6. Collect team commits (not yours) → list top 20 in the same file
7. Update `MEMORY.md` index
8. Pop stash

**Output:** `.claude/memory/commits/<YYYY-MM-DD>.md` with your commits + team context.

---

### `scripts/save-session-memory.sh`

**Usage:** `./save-session-memory.sh [optional-summary-text]`

Manually save session context to memory. Called automatically by `state-breadcrumb.sh` (SessionEnd hook) or run manually after significant work.

**Input:** Optional summary text string

**Output:** Appends to `.claude/memory/sessions/<YYYY-MM-DD>.md`; updates `MEMORY.md` index.

---

## Templates reference

Templates in `templates/` are copied into each project by `init.sh` or `/project-init`.

### `SUMMARY.template.md`

The central artifact for every non-trivial task. Fields:

| Field | Who fills it | Purpose |
|-------|-------------|---------|
| `Lane:` | Coordinator | tiny / normal / high-risk — drives ceremony |
| `Confidence:` | Coordinator | high / medium / low — drives whether human is asked |
| `## What changed` | Implementer/Debugger/Refactorer | Description of the change |
| `## Rationale` | Planner | Why this approach |
| `## Alternatives considered` | Planner | What else was considered |
| `## Deviations` | Any agent | Autonomous fixes under Rules 1–3 |
| `## Verify` | Implementer + Verifier | Table of commands to run (with expected exit codes) |
| `## Rollback` | Implementer | `git revert <sha>` or equivalent |
| `## Harness-Delta` | Any agent | Changes to `.claude/` config |

---

### `TEST_MATRIX.template.md`

Tracks behavior coverage across test types. One row per behavior.

| Column | Values |
|--------|--------|
| `Behavior` | Description of expected behavior |
| `Contract` | yes / no (is this a public contract?) |
| `Unit` | yes / no |
| `Integration` | yes / no |
| `E2E` | yes / no |
| `Status` | planned → in_progress → implemented → changed → retired |
| `Evidence` | test path, Verify row reference, or commit sha |

Rule: Evidence cannot be `none` for `implemented` rows.

---

### `ESCALATIONS.template.md`

Records hard-gate decisions that require human input. Default: deny-on-no-response (unresolved entries block all dispatch).

Each entry (E001, E002, …) has:
- `raised_by`, `date`, `trigger`, `question`, `context`
- `options` (A/B choices with consequences)
- `default_if_no_response: BLOCK`
- `decision: pending` (or the decision once made)

---

### `settings.json.template`

Full permissions + deny list + hook registrations. Applied by `init.sh`.

**Allowed by default:** `Bash(*)`, `Read(*)`, `Edit(*)`, `Write(*)`, `WebFetch(*)`, `WebSearch(*)`

**Denied (always require user confirmation):**

| Command | Why |
|---------|-----|
| `rm -rf *`, `rm -r *` | Irreversible mass delete |
| `git push --force`, `git push -f` | Overwrites remote history |
| `git reset --hard` | Discards uncommitted work |
| `git clean -f` | Deletes untracked files |
| `git push * main`, `git push * master` | Direct push to protected branches |
| `git branch -D *` | Force-deletes branch |
| `kill -9 *`, `killall *` | Force-terminates processes |
| `npm publish`, `pnpm publish` | Releases to public registry |
| `sudo *` | Privilege escalation |
| `curl * \| bash`, `wget * \| bash` | Remote code execution |

---

## Memory system

Memory persists context across sessions. All memory files live in `.claude/memory/` and follow a frontmatter format:

```markdown
---
name: <slug>
description: <one-line summary>
metadata:
  type: user | feedback | project | reference
---

<content>
```

### Memory types

| Type | What it stores | When saved |
|------|---------------|-----------|
| `user` | Role, goals, preferences, knowledge level | When user profile details are learned |
| `feedback` | Corrections and validated approaches | When user corrects Claude or confirms an approach |
| `project` | Active goals, decisions, deadlines | When project state changes |
| `reference` | Pointers to external resources (Linear, Grafana, etc.) | When external system locations are mentioned |

### Memory lifecycle

```
session starts
  ↓ MEMORY.md loaded into context (every session)
  ↓ specs/HANDOFF.md read if exists → deleted
  ↓
work happens
  ↓
git commit
  ↓ save-commit-memory.sh → .claude/memory/commits/YYYY-MM-DD.md
  ↓
session ends
  ↓ state-breadcrumb.sh → .claude/memory/sessions/YYYY-MM-DD.md
  ↓ session-handoff.sh → specs/HANDOFF.md
  ↓
user corrects Claude or confirms approach
  ↓ Claude saves feedback memory → .claude/memory/feedback/
  ↓
team project: next day
  ↓ /sync-memory → git pull + scan commits + flag overlaps
```

### `MEMORY.md` index

Loaded into every session's context. The index must stay under 200 lines. Format:

```markdown
# Memory Index

- [Title](path/to/file.md) — one-line hook explaining what's in the file
```

---

## The coordinator flow

How all components work together for a typical feature request:

```
User: "add CSV export to the reports page"

1. scope-gate.sh fires
   → detects "add" (implementation intent)
   → no high-risk words
   → injects AUTO-COORDINATOR context with "Likely lane: tiny or normal"

2. Coordinator (auto-active) wakes up
   → Step 0: loads .claude/docs/ (architecture, conventions, stack, entry-points)
   → Step 1: loads docs/solutions/INDEX.md for prior learnings
   → Step 2: classifies → new-feature · Lane: normal · Confidence: 4/5

3. TaskCreate board created (all steps, before any work):
   #1 Planner: design CSV export approach
   #2 Implementer: build export endpoint + UI
   #3 Verifier: confirm export works

4. Specs initialized:
   → specs/add-csv-export/SUMMARY.md (Lane: normal, Confidence: high)
   → specs/add-csv-export/TEST_MATRIX.md (planned rows)
   → specs/add-csv-export/ESCALATIONS.md (empty)

5. Wave 1: Planner (sonnet)
   → reads docs, finds relevant files
   → writes PLAN.md with wave-organized tasks

6. Wave 2: Implementer (sonnet)
   → follows PLAN.md precisely
   → writes code, writes tests
   → fills SUMMARY.md "What changed" + "Verify" table

7. Commit: git commit
   → commit-quality-gate.sh: no secrets, no debug artifacts → ALLOW
   → risk-corroboration.sh: Lane=normal, no hard-gate signals → ALLOW
   → save-commit-memory.sh: writes to memory/commits/ → ALLOW

8. Wave 3: Verifier (sonnet)
   → runs every command in SUMMARY.md Verify table
   → reports PASS

9. Session end (Stop hook):
   → session-handoff.sh writes specs/HANDOFF.md
   → state-breadcrumb.sh appends to memory/sessions/

10. Next session:
    → reads HANDOFF.md → deletes it → continues from "Next steps"
```

---

## Risk lanes & hard gates

### Lanes

| Lane | Criteria | Process |
|------|----------|---------|
| `tiny` | Single file, no external contracts, reversible, <30 min | Direct edit; hooks are safety net |
| `normal` | Multi-file, internal API changes, moderate complexity | Research brief + plan before coding |
| `high-risk` | Auth, migration, public contract, payment, security, `.claude/` | Full chain: research → plan → confirm → build → review |

### Hard gates (always `high-risk`, cannot self-downgrade)

Any of these forces `high-risk` regardless of scope:
- Authentication / authorization
- Data loss / schema migration
- Audit / security controls
- External provider behavior (Stripe, Twilio, SendGrid, AWS)
- Public API contract changes (adding/removing/renaming fields)
- Removing or weakening validation
- Touching `.claude/` config files or hooks
- Multi-domain changes

### Stopping rules

The coordinator stops and asks the human when:
- Confidence drops below medium
- A hard gate is discovered mid-task
- Scope needs to expand beyond the plan
- An unresolved `ESCALATIONS.md` entry exists (`decision: pending`)
- Verifier fails twice in a row
- A teammate's recent commit conflicts with the planned approach

---

## Extending the harness

### Add a new skill

```bash
mkdir -p skills/<name>
cat > skills/<name>/SKILL.md << 'EOF'
---
name: <name>
description: <trigger condition — when to invoke this>
model: sonnet | haiku
effort: high | medium | low
---

# <Name>

**Invoke:** `/<name> [args]`

## Step 1 — ...
## Step 2 — ...
EOF

# Install globally
cp -r skills/<name> ~/.claude/skills/
```

The `description` field is used by Claude Code to auto-invoke the skill. Make it a specific, actionable trigger phrase.

### Add a new rule

```bash
cat > rules/<name>.md << 'EOF'
# <Name> Rules

## Rule 1
<imperative instruction>

## Rule 2
<imperative instruction>
EOF

cp rules/<name>.md ~/.claude/rules/
```

Rules must be imperative ("do X", "never Y") — not descriptive. Reference them in `CLAUDE.md`.

### Add a new hook

```bash
cat > hooks/<name>.sh << 'EOF'
#!/bin/bash
# <name>.sh — <description>
# Trigger: <PreToolUse|PostToolUse|UserPromptSubmit|Stop>(<matcher>)
# Exit 2 to block, 0 to allow

INPUT=$(cat /dev/stdin)
# ... your logic ...

exit 0
EOF

chmod +x hooks/<name>.sh
cp hooks/<name>.sh ~/.claude/hooks/

# Register in ~/.claude/settings.json under the appropriate event
```

Hook exit codes: `0` = allow, `2` = block. Never exit `1` (reserved for errors).

### Add a stack-specific rule

```bash
cat > rules/stacks/<name>.md << 'EOF'
# <Stack Name> Rules
...
EOF

# Add detection in scripts/init.sh:
has_signal "<name>" && cp "$HARNESS_DIR/rules/stacks/<name>.md" "$CLAUDE_DIR/rules/<name>.md" || true

# Add signal detection in detect_stack():
grep -qi "<keyword>" "$req" "$pyp" 2>/dev/null && SIGNALS+=("<name>")
```

### Update an existing project after harness changes

```bash
~/.claude-harness/scripts/init.sh /path/to/project
# The script will warn before overwriting existing settings.json
```
