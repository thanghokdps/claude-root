# Claude Harness — Usage Guide

From first install to running daily tasks.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Step 1 — Install the harness (once)](#3-step-1--install-the-harness-once)
4. [Step 2 — Bootstrap a new project](#4-step-2--bootstrap-a-new-project)
5. [Step 3 — Fill in project info after init](#5-step-3--fill-in-project-info-after-init)
6. [Step 4 — First working session](#6-step-4--first-working-session)
7. [Daily workflow](#7-daily-workflow)
8. [Common tasks](#8-common-tasks)
9. [Team workflow](#9-team-workflow)
10. [Ending a session](#10-ending-a-session)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Overview

Claude Harness is a governance framework for Claude Code. It has two layers:

```
┌─────────────────────────────────────────────────────┐
│  SKILLS (engine)                                    │
│  /feature · /fix-bug · /code-review · /ticket ...  │
│  → answers "how do I do this?"                      │
├─────────────────────────────────────────────────────┤
│  HARNESS (control)                                  │
│  hooks · rules · memory                             │
│  → answers "how careful? who must approve?"         │
└─────────────────────────────────────────────────────┘
```

**Core principle:** Ceremony increases with risk. Human interruption increases with ambiguity.

**General flow:**

```
user prompt
  → scope-gate.sh        classify risk, check old memory
  → /coordinator         analyze request, route to the right agent
  → Explorer / Planner   understand code, build plan
  → Implementer          write code
  → Verifier / Reviewer  verify result
  → commit hooks         block bad commits
  → memory hooks         save history
```

---

## 2. Prerequisites

| Item | Requirement |
|------|-------------|
| Claude Code | CLI or desktop app (https://claude.ai/code) |
| Git | `git --version` must work |
| `jq` | `brew install jq` (used by hooks) |
| Python 3.12 | Only needed for **headroom** (context compression) |
| Node.js / Python / Go | Depends on your project stack |

---

## 3. Step 1 — Install the harness (once)

### Download and run install

```bash
# Clone or download the repo to ~/Downloads/Claude
# (you can rename or place it elsewhere)

bash ~/Downloads/Claude/scripts/install.sh
```

**The script will ask if it already exists.** Type `y` to overwrite, `n` to keep existing.

Default install location is `~/.claude-harness`. To install elsewhere:

```bash
bash ~/Downloads/Claude/scripts/install.sh ~/my-tools/claude-harness
```

### Result after install

```
🔧 Claude Harness Installer
   Source : ~/Downloads/Claude
   Target : ~/.claude-harness

✅ Harness copied to ~/.claude-harness
   Added HARNESS_DIR to .zshrc

📦 Installing to ~/.claude/ ...
   Skills  : 18 installed
   Rules   : 13 installed
   Hooks   : 9 installed
   Memory  : templates copied

✅ Installation complete!
```

### Reload shell

```bash
source ~/.zshrc     # or open a new terminal
echo $HARNESS_DIR   # should print ~/.claude-harness
```

### (Optional) Install headroom — context compression

Reduces token usage by 60–95% when the context window grows large:

```bash
bash $HARNESS_DIR/scripts/setup-headroom.sh
```

**Requires:** Python 3.12 (`brew install python@3.12`).

After install, the `headroom-compress.sh` hook triggers automatically when output exceeds 8KB.

---

## 4. Step 2 — Bootstrap a new project

Run **once** per project to create a dedicated `.claude/` workspace.

### Method A — Via Claude Code (recommended)

```bash
cd ~/my-project

# Open Claude Code and type:
/project-init
```

Claude will:
1. Scan `src/`, `package.json`, `requirements.txt`… to detect the stack
2. Create the full `.claude/` workspace (docs, agents, hooks, rules, skills, templates)
3. Generate a project-specific `CLAUDE.md` with real paths and commands

### Method B — Via script

```bash
cd ~/my-project
$HARNESS_DIR/scripts/init.sh

# Or specify the path explicitly:
$HARNESS_DIR/scripts/init.sh /path/to/my-project
```

### Method C — Use an existing stack bundle (React Native / Next.js / Python)

If your project matches one of the bundles in `stacks/`:

```bash
# Example: React Native project
cp -r $HARNESS_DIR/stacks/react-native/.claude ~/my-rn-project/
```

Then edit the files to match your project's actual paths.

### Auto-detected stack signals

| Signal | When |
|--------|------|
| `typescript` | `tsconfig.json` or `"typescript"` in package.json |
| `react` | `"react"` in package.json |
| `jest` | `"jest"` in package.json |
| `nextjs` | `"next"` in package.json |
| `python` | `requirements.txt` or `pyproject.toml` |
| `fastapi` | `fastapi` in requirements |
| `langgraph` | `langgraph` in requirements |

### Result after bootstrap

```
your-project/
├── CLAUDE.md                  ← needs to be filled in
└── .claude/
    ├── settings.json          ← hooks registered
    ├── docs/                  ← knowledge base (written by /project-init)
    │   ├── index.md
    │   ├── architecture.md
    │   ├── conventions.md
    │   ├── stack.md
    │   ├── entry-points.md
    │   └── test-strategy.md
    ├── rules/                 ← universal + stack-specific rules
    ├── skills/                ← slash commands for this project
    ├── hooks/                 ← automation scripts
    └── memory/
        ├── MEMORY.md          ← index (auto-loaded every session)
        ├── user.md            ← needs to be filled in
        └── project/
            └── context.md     ← needs to be filled in
```

---

## 5. Step 3 — Fill in project info after init

**This is the most important step.** Claude only works well when it has the right context.

### 5.1 — Fill in `CLAUDE.md`

Open `CLAUDE.md` in the project root and fill in the sections with `<!-- ... -->` comments:

```markdown
## What this project is
Internal order management app for the logistics team.
Stack: Next.js 14 App Router + PostgreSQL + Prisma.

## Run the project
```bash
pnpm install
pnpm dev           # dev server at localhost:3000
pnpm test          # jest
pnpm typecheck     # tsc --noEmit
pnpm lint          # eslint
```

## Architecture
src/app/          ← Next.js App Router (Server Components by default)
src/components/   ← Client Components ("use client")
src/lib/          ← utilities, db client
src/server/       ← Server Actions

## Constraints
- TypeScript strict — npx tsc --noEmit must pass before commit
- pnpm only — do not use npm or yarn
- Do not call DB directly in route handlers — use Server Actions
```

### 5.2 — Fill in `.claude/memory/user.md`

```markdown
## Role & Background
Senior fullstack engineer. Comfortable with Next.js and PostgreSQL.
Currently learning Server Components and React v19 patterns.

## Preferences
- Short, concise responses — no need to explain every obvious step
- TypeScript strict — never use `any`
- Commit messages in format: feat/fix/chore: short description
```

### 5.3 — Fill in `.claude/memory/project/context.md`

```markdown
## Goals
MVP checkout flow for mobile app. Deadline: 2026-07-01.

## Active decisions
- Use Server Actions instead of a separate REST API — **Why:** reduces boilerplate,
  type-safe end-to-end — **How to apply:** all mutations go through actions/

## Constraints
- Do not use Vercel AI SDK — currently using CopilotKit
- Firebase config must not be committed (already gitignored)

## Team
- Thang: frontend + backend
- Mai: designer, sends Figma links via Slack
```

---

## 6. Step 4 — First working session

### Open Claude Code in the project

```bash
cd ~/my-project
claude          # CLI
# or open the Claude Code desktop app and select the folder
```

### Verify context loaded correctly

Claude automatically reads `CLAUDE.md` and `MEMORY.md` each session. Quick check:

```
what project are you working on?
```

Claude should answer with the correct project name, stack, and constraints.

### Verify hooks are working

```bash
# Try committing a normal file — hooks will check it
git add README.md
git commit -m "test: verify hooks"
# No issues → commit passes
# Secret or console.log detected → commit blocked with a clear message
```

---

## 7. Daily workflow

### Start a session

```bash
cd ~/my-project
claude
```

If you left work unfinished yesterday, `specs/HANDOFF.md` will auto-load and Claude will know where to continue.

If working in a team — run sync first:

```
/sync-memory
```

### During the session

**Auto-coordinator is always on** — you do not need to type `/coordinator`. Just describe what you want:

```
add CSV export to the reports page
```

Claude will automatically:
1. Classify the task (lane: tiny / normal / high-risk)
2. Create the task board
3. Route to the right agent
4. Execute in waves
5. Verify the result

---

## 8. Common tasks

### Implement a new feature

```
add dark mode to the settings page
```

Or more explicitly:

```
/feature add dark mode to the settings page
```

**Flow:** risk intake → research → plan → build → self-review → commit

For complex features (auth, payment, migration) — Claude will ask for confirmation before proceeding.

---

### Fix a bug

```
/fix-bug app crashes when uploading files larger than 10MB
```

**Flow:** reproduce → root cause (no guessing, real trace) → minimal fix → verify → commit

Commit message auto-generated: `fix: <what was wrong and what was fixed>`

---

### Code review

```bash
# Review the full current branch
/code-review

# More thorough review
/code-review high

# Quick scan, critical issues only
/code-review low
```

**Output:**
```
### 🔴 MUST FIX — SQL injection
File: src/users/repo.ts:42
Issue: user input concatenated directly into SQL string
Fix: use parameterized query: db.query('...', [id])

### 🟡 SHOULD FIX — missing error boundary
...
```

---

### Implement from a ticket (5-agent pipeline)

```
/ticket #123 add swipe-to-dismiss on pending request cards
```

**Automated pipeline:**
```
PM Agent      → read ticket, find relevant code, identify risks
    ↓
Architect     → technical plan with wave-organized tasks
    ↓
Developer     → implement following the plan (parallel waves)
    ↓
Reviewer      → review diff, APPROVED or request changes
    ↓
QA/Verifier   → lint + types + tests + golden path + commit
```

---

### Write tests

```
/gen-tests src/services/payment-service.ts
```

Or ask directly:

```
write unit tests for the calculateDiscount function in src/utils/pricing.ts
```

---

### Create a component from Figma

```
/figma-to-screen [Figma URL]
```

---

### Small task, no ceremony needed

```
/task change primary button color from blue-600 to indigo-600
```

**Flow:** read conventions → implement → verify → commit. No plan needed.

---

### Brainstorm before a complex feature

```
/brainstorming design a real-time notification system
```

**Flow:** asks one question at a time → proposes 2–3 approaches → designs → writes `specs/<slug>/design.md` → calls `/writing-plans`

---

### Generate an implementation plan from a design

```
/writing-plans
```

Run after `/brainstorming`. Generates `specs/<slug>/PLAN.md` with wave-organized tasks.

---

### Generate a PR description

```
/create-pr
```

Generates `PR_TEMPLATE.md` — pre-filled with title, summary (why not how), files changed, test plan.

---

### Dynamic workflow — large-scale tasks

When a task requires 10+ independent file changes, a codebase-wide audit, or a large migration → use a dynamic workflow instead of regular wave agents.

**Trigger:**
```
ultracode: audit all API endpoints in src/routes/ for missing auth checks
```

Or use the harness `/workflow` command:
```
/workflow migrate all class components to functional
```

**Claude Code will:**
1. Write a JavaScript orchestration script
2. Execute the script in the background (session stays responsive)
3. Spawn up to 16 agents in parallel, up to 1000 agents per run

**Monitor:**
```
/workflows        list all running workflows
p                 pause / resume
x                 stop
s                 save script as a reusable command
```

**Save for reuse:**
- `.claude/workflows/<name>.js` — shared with team via git
- `~/.claude/workflows/<name>.js` — personal, available in all projects

Saved workflows become `/<name>` commands in autocomplete.

**Built-in workflow:**
```
/deep-research your question here
```

Fan-out web searches → cross-check sources → adversarial vote on each claim → cited report.

> **Cost note**: Dynamic workflows use significantly more tokens. Test on a small directory before running against the full codebase.

---

## 9. Team workflow

### At the start of each session

```
/sync-memory
```

Or run the script directly:

```bash
$HARNESS_DIR/scripts/sync-team.sh
```

**What it does:**
1. Stash uncommitted changes
2. `git fetch --all --prune` + `git pull`
3. Scan **your** commits since the last sync → save to memory
4. List teammate commits → flag files that were touched
5. Pop stash

**View the result:**

```bash
cat .claude/memory/commits/$(date +%Y-%m-%d).md
```

You'll see your commits plus a list of team changes. If a file was touched by both you and a teammate, Claude will warn you.

---

## 10. Ending a session

### Before closing — compact the session

```
/compact
```

**What it does:**
1. Summarizes what was done in the session
2. Writes `specs/HANDOFF.md` (auto-read by the next session)
3. Merges important learnings into `docs/solutions/`
4. Updates memory if user preferences were learned

**Next session:** Claude auto-reads `HANDOFF.md` → knows where to continue → deletes the file.

### After a large session — compound learnings

```
/compound
```

Use after sessions with complex debugging, hard bugs, or architectural decisions. Saves to `docs/solutions/` so future sessions don't repeat the same mistakes.

---

## 11. Troubleshooting

### Commit blocked by quality gate

```
🚫 COMMIT BLOCKED — quality gate failed:
   ❌ OpenAI API key pattern detected in staged code
```

**Fix:**
```bash
# Find the file with the issue
git diff --cached | grep -n "sk-"

# Remove the key, use an env var instead
# .env file → gitignored → read from process.env

# Re-stage and commit
git add <file>
git commit -m "..."
```

---

### Hook triggering a false positive

Example: a test file with `"api_key": "test-value"` gets blocked.

**Short-term fix** — bypass for that commit (use with care):
```bash
SKIP_QUALITY_GATE=1 git commit -m "test: add fixture with api key pattern"
```

**Long-term fix** — update the hook to skip the pattern:
```bash
# .claude/hooks/commit-quality-gate.sh
# Add to the STAGED_APP section:
':!*.fixture.*' ':!tests/fixtures/*'
```

---

### `specs/HANDOFF.md` not loading

Check that `CLAUDE.md` contains this line:

```bash
cat specs/HANDOFF.md 2>/dev/null && rm -f specs/HANDOFF.md
```

If missing → add it to the "Session Resume" section in `CLAUDE.md`.

---

### Claude doesn't remember context from the previous session

1. Check `MEMORY.md` still has entries: `cat .claude/memory/MEMORY.md`
2. Check `HANDOFF.md` was deleted (if it still exists → Claude hasn't read it yet)
3. `/compact` was not run → nothing was saved

---

### Memory index too long (> 200 lines)

Claude Code truncates `MEMORY.md` after 200 lines:

```bash
# Count lines
wc -l .claude/memory/MEMORY.md

# Remove old entries (> 30 days, no longer applicable)
# Delete the linked memory file first, then remove the line from MEMORY.md
```

---

### Update the harness after source changes

```bash
# Re-run install.sh — auto-detects and updates
bash $HARNESS_DIR/scripts/install.sh
```

To update `.claude/` for a specific project:

```bash
cd ~/my-project
$HARNESS_DIR/scripts/init.sh
# Script will warn before overwriting settings.json
```

---

## Full flow diagram

```
┌─ INSTALL (once) ────────────────────────────────────────────┐
│                                                              │
│  bash ~/Downloads/Claude/scripts/install.sh                 │
│  source ~/.zshrc                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─ BOOTSTRAP PROJECT (once per project) ──────────────────────┐
│                                                             │
│  cd ~/my-project                                           │
│  /project-init              ← Claude Code                  │
│  # or: $HARNESS_DIR/scripts/init.sh                       │
│                                                             │
│  Fill in CLAUDE.md          ← run commands, architecture   │
│  Fill in memory/user.md     ← role, preferences            │
│  Fill in memory/project/*.md ← goals, decisions            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─ EVERY SESSION ─────────────────────────────────────────────┐
│                                                             │
│  Start:                                                     │
│    claude                   ← open Claude Code             │
│    /sync-memory             ← if working in a team         │
│    (reads HANDOFF.md automatically if present)             │
│                                                             │
│  Work:                                                      │
│    "add feature X"          ← auto-coordinator handles it  │
│    /fix-bug <symptom>       ← debug flow                   │
│    /code-review             ← review before PR             │
│    /ticket #123 <desc>      ← full 5-agent pipeline        │
│                                                             │
│  End:                                                       │
│    /compact                 ← save session state           │
│    /compound                ← after a session with big learnings │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
                   Next day:
                   New session auto-reads HANDOFF.md
                   → continues from "Next steps"
```

---

## Cheat sheet — most-used commands

| Command | When to use |
|---------|-------------|
| `/project-init` | First-time project setup |
| `/sync-memory` | Start of session when working in a team |
| `/feature <description>` | Implement a new feature |
| `/fix-bug <symptom>` | Debug and fix a bug |
| `/code-review` | Review before pushing a PR |
| `/code-review high` | Thorough review for important PRs |
| `/ticket #N <description>` | Run the full pipeline from a ticket |
| `/task <description>` | Small fix, no ceremony needed |
| `/brainstorming <idea>` | Design before building a complex feature |
| `/writing-plans` | After brainstorming, generate PLAN.md |
| `/create-pr` | Generate a PR description |
| `/checkpoint` | Check progress mid-session |
| `/compact` | End of session, save state |
| `/compound` | After a large session, save learnings |
| `/btw <question>` | Quick question without breaking the flow |
