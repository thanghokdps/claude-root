# Claude Harness — General Skills Library

A portable harness that auto-generates a project-specific `.claude/` config by scanning your `src/` directory. Works with any tech stack.

## Install (one time)

```bash
cp -r ~/Downloads/Claude ~/.claude-harness
chmod +x ~/.claude-harness/scripts/*.sh
chmod +x ~/.claude-harness/hooks/*.sh
```

## Bootstrap a new project

**Option A — via Claude Code (recommended):**
```bash
cd my-project
cp ~/.claude-harness/CLAUDE_LEGACY.md ./CLAUDE.md
# Open Claude Code, then run:
# /init-project
```

**Option B — via script:**
```bash
cd my-project
~/.claude-harness/scripts/init.sh
```

Both options do the same thing:
1. Scan `src/` for tech stack signals (Node.js, Python, Go, LangGraph, Prisma, etc.)
2. Copy appropriate rules, skills, hooks into `.claude/`
3. Write `.claude/settings.json` with all hooks registered
4. Bootstrap `.claude/memory/` with MEMORY.md index
5. Generate project `CLAUDE.md` from template

## What gets generated

```
your-project/
├── CLAUDE.md                    ← Fill in: run commands, architecture, constraints
└── .claude/
    ├── settings.json            ← Hooks auto-registered
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

## Skill reference

| Skill | Command | When to use |
|-------|---------|-------------|
| **init-project** | `/init-project` | Bootstrap .claude/ for a new project |
| **feature** | `/feature <description>` | Implement any new feature |
| **fix-bug** | `/fix-bug <symptom>` | Fix a specific bug |
| **code-review** | `/code-review [low\|medium\|high]` | Review current branch diff |
| **checkpoint** | `/checkpoint` | Check progress + run quality gates |
| **sync-memory** | `/sync-memory` | Team project: pull latest + update memory |

## Hook reference

| Hook | When it fires | What it does |
|------|--------------|--------------|
| `commit-quality-gate.sh` | Before `git commit` | Blocks: secrets, .env files, breakpoints, large binaries |
| `branch-guard.sh` | Before `git push` | Blocks force-push to main; warns on direct push |
| `save-commit-memory.sh` | After `git commit` | Saves commit hash + files to `.claude/memory/commits/` |
| `state-breadcrumb.sh` | Session end | Appends session summary to `.claude/memory/sessions/` |
| `scope-gate.sh` | Each prompt | Flags high-risk patterns; warns on stale memory |

## Team workflow

```bash
# Start of each session on a shared repo:
# /sync-memory
# OR:
.claude/hooks/sync-team.sh
```

This:
1. `git pull` the latest
2. Finds your last recorded commit
3. Scans YOUR commits since then → writes to memory
4. Lists team commits → highlights files you both touched

## Memory workflow

Memory saves automatically via hooks. You can also save manually:

```bash
# Save a session note
.claude/harness/scripts/save-session-memory.sh "what I worked on today"
```

Feedback memories (corrections, validated approaches) are saved via Claude:
> "Remember: don't mock the database in tests — we got burned when mock/prod diverged"

Claude will save to `.claude/memory/feedback/YYYY-MM-DD.md`.

## Detecting stale memory

The `scope-gate.sh` hook fires on every prompt and warns if:
- Team project + last sync > 2 days ago → "run /sync-memory"
- Unreviewed feedback memories exist → "check before starting"

## Adding stack-specific rules

Create `~/.claude-harness/rules/stacks/<name>.md`.
Add detection in `scripts/init.sh`:
```bash
has_signal "mystack" && cp "$HARNESS_DIR/rules/stacks/mystack.md" "$CLAUDE_DIR/rules/mystack.md"
```

## Structure of this repo

```
~/.claude-harness/
├── CLAUDE_LEGACY.md         ← Copy this as CLAUDE.md into any new project
├── HARNESS.md               ← How the harness works (philosophy)
├── README.md                ← This file
├── scripts/
│   ├── init.sh              ← Main bootstrap script
│   ├── sync-team.sh         ← Team sync: pull + memory rebuild
│   └── save-session-memory.sh
├── skills/                  ← Generic skills (copied into .claude/skills/)
├── agents/                  ← Sub-agent role definitions
├── rules/                   ← Universal + stack-specific rules
├── hooks/                   ← All hook scripts
├── memory/                  ← Memory templates
└── templates/               ← CLAUDE.md, settings.json templates
```
