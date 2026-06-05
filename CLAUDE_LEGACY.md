# Claude Harness — Genesis Template

> **Copy this file as `CLAUDE.md` into any new project**, then run `init-project` to auto-generate the full `.claude/` harness from your `src/` scan.

---

## Bootstrap a new project

```bash
# 1. Copy this file into your project root
cp ~/.claude-harness/CLAUDE_LEGACY.md ./CLAUDE.md

# 2. Tell Claude to run the init skill
# /init-project

# OR run the script directly:
~/.claude-harness/scripts/init.sh
```

The `init-project` skill will:
1. Scan `src/` to detect your tech stack and architecture patterns
2. Copy appropriate rules, skills, hooks into `.claude/`
3. Generate a project-specific `CLAUDE.md` (replaces this file)
4. Bootstrap the memory system at `.claude/memory/`
5. Write `.claude/settings.json` with all hooks registered

---

## Harness philosophy

> **Ceremony scales with risk. Human interruption scales with ambiguity.**

Two independent dials:
- **Risk** decides how much proof and process a change carries (lane: tiny / normal / high-risk)
- **Ambiguity** decides whether a human is asked — never to classify risk, only to confirm intent

A high-risk-but-clear change runs autonomously through heavy proof.  
A tiny-but-unclear change still pauses to ask.

### The 10-flag risk checklist

| Flag | Examples |
|------|----------|
| Auth / authorization | login, JWT, roles, permissions |
| Data model change | schema migration, new table/collection |
| External provider | new SDK, 3rd-party API, payment, AI model |
| Public contract change | REST endpoint rename, breaking type change |
| Audit / security | sanitization, validation removal, PII |
| Cross-platform impact | shared lib, monorepo, mobile + web |
| Existing behavior change | modifies path already covered by tests |
| Weak test coverage | area with < 50% coverage |
| High-blast file | config, shared middleware, CI pipeline |
| Multi-domain effect | touches 4+ modules or services |

- **0–1 flags** → tiny lane (direct edit, no plan)
- **2–3 flags** → normal lane (plan + review)
- **4+ flags or any hard gate** → high-risk (full chain: research → plan → build → review)

Hard gates (always high-risk, cannot self-downgrade): auth, data-loss/migration, audit/security, public contract, high-blast file.

---

## Skill catalog

| Skill | Invoke | Purpose |
|-------|--------|---------|
| `init-project` | `/init-project` | Scan src → generate full .claude/ harness |
| `feature` | `/feature <description>` | Intake → plan → build → review |
| `fix-bug` | `/fix-bug <symptom>` | Root cause → minimal fix → verify → commit |
| `code-review` | `/code-review [low\|medium\|high]` | Review diff for bugs + cleanups |
| `checkpoint` | `/checkpoint` | Check progress vs plan; run quality gates |
| `sync-memory` | `/sync-memory` | Pull latest + rebuild memory from your commits |

---

## Hook catalog

Registered in `.claude/settings.json`. Run automatically at lifecycle events.

| Hook | Trigger | Does |
|------|---------|------|
| `commit-quality-gate.sh` | PreToolUse(Bash: git commit) | Block secrets, debug code |
| `branch-guard.sh` | PreToolUse(Bash: git push) | Warn on push to main/master |
| `state-breadcrumb.sh` | SessionEnd | Append session summary to memory |
| `scope-gate.sh` | UserPromptSubmit | Flag out-of-scope requests |
| `save-commit-memory.sh` | PostToolUse(Bash: git commit) | Save commit to memory index |

---

## Memory system

Memory lives at `.claude/memory/` — file-based, persists across sessions.

```
.claude/memory/
├── MEMORY.md              # Index — loaded every session
├── user.md                # User profile, preferences
├── feedback/              # Corrections + validated approaches
│   └── YYYY-MM-DD.md
├── project/               # Decisions, goals, deadlines
│   └── context.md
├── commits/               # Auto-saved after each commit
│   └── YYYY-MM-DD.md
└── sessions/              # Session breadcrumbs (from state-breadcrumb hook)
    └── YYYY-MM-DD.md
```

**Auto-save triggers:**
- After `git commit` → saves hash, message, files changed to `commits/`
- On session end → saves session summary to `sessions/`
- On explicit feedback → saves to `feedback/`

**Team sync (`/sync-memory`):**
1. `git fetch --all && git pull`
2. Find your last commit: `git log --author="<you>" -1`
3. Collect all your commits from last known → HEAD
4. Update memory with what changed, decisions made, unresolved items

---

## Rules catalog

Copied into `.claude/rules/` during `init-project`. Stack-specific rules are added automatically.

| Rule file | Applies to |
|-----------|-----------|
| `git.md` | All projects |
| `testing.md` | All projects |
| `orchestration.md` | All projects |
| `memory.md` | All projects |
| `typescript.md` | TypeScript projects |
| `python.md` | Python projects |
| `langgraph.md` | LangGraph projects |
| `nextjs.md` | Next.js projects |
| `api.md` | Projects with REST/GraphQL APIs |

---

## Environment variables (minimal required set)

```env
# Filled during init-project based on stack detection
AI_PROVIDER=          # openai | anthropic | ollama
OPENAI_API_KEY=       # if openai
ANTHROPIC_API_KEY=    # if anthropic
DATABASE_URL=         # if DB detected
```

---

## Constraints (universal)

- **TypeScript strict** — `npx tsc --noEmit` before any commit (if TS project)
- **Never commit secrets** — enforced by `commit-quality-gate.sh`
- **Mutation tools need HITL** — never call mutation tools without user confirmation gate
- **`temperature: 0`** on all models used for routing and structured output
- **pnpm / npm / yarn** — use whatever the project uses (detected from lock file)
