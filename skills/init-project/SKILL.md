# init-project — Bootstrap .claude/ harness from src/ scan

**Invoke:** `/init-project`

**What it does:** Scan the project's `src/` directory to detect tech stack and patterns, then auto-generate an appropriate `.claude/` harness config (rules, skills, hooks, memory, settings.json) and project `CLAUDE.md`.

---

## Stage 0 — Pre-flight

1. Locate the harness library: `~/.claude-harness/` (or `HARNESS_DIR` env var)
2. If not installed, abort and print install instructions
3. Verify we are in a git repo root (check for `.git/`)

## Stage 1 — Scan

Scan the project to answer:
1. **Language** — Node.js / Python / Go / Java / Rust / other?
2. **Framework** — Next.js / Express / FastAPI / Django / NestJS / other?
3. **AI/ML layer** — LangGraph / LangChain / CopilotKit / OpenAI SDK / Anthropic SDK?
4. **Database** — Prisma / SQLAlchemy / Mongoose / Postgres / Redis / LanceDB?
5. **Test framework** — Vitest / Jest / Pytest / Playwright?
6. **Package manager** — pnpm / yarn / npm / pip / poetry?

Run: `~/.claude-harness/scripts/init.sh`

If the script is unavailable, perform detection manually:
```bash
# Check manifests
cat package.json 2>/dev/null | grep -E '"(next|react|typescript|langchain|prisma|vitest|jest)"'
cat requirements.txt 2>/dev/null | grep -iE "fastapi|django|langchain|langgraph"
ls src/ 2>/dev/null | head -20
```

## Stage 2 — Generate

From detected signals, copy into `.claude/`:

| Detected | Copy |
|----------|------|
| Always | `rules/git.md`, `rules/testing.md`, `rules/orchestration.md`, `rules/memory.md` |
| `typescript` | `rules/stacks/typescript.md` |
| `python` | `rules/stacks/python.md` |
| `langgraph` | `rules/stacks/langgraph.md` |
| `nextjs` | `rules/stacks/nextjs.md` |
| `prisma` | `rules/stacks/prisma.md` |

Write `.claude/settings.json` from `templates/settings.json.template` with:
- Universal hooks wired (commit-quality-gate, branch-guard, state-breadcrumb, scope-gate, save-commit-memory)
- Stack-specific hooks added (ruff for Python, eslint for TS)
- Common `allow` permissions pre-populated for detected package manager

## Stage 3 — Memory bootstrap

Create `.claude/memory/` structure:
```
.claude/memory/
├── MEMORY.md          # Index
├── user.md            # Pre-filled with git user.name + email
├── feedback/          # (empty, ready)
├── project/
│   └── context.md    # Pre-filled with project name + detected stack
├── commits/           # (empty, ready)
└── sessions/          # (empty, ready)
```

## Stage 4 — Generate CLAUDE.md

Write `CLAUDE.md` from `templates/CLAUDE.md.template`:
- Project name from directory name
- Detected stack list
- Placeholder sections for: run commands, architecture, key directories, constraints
- Skill table (feature, fix-bug, code-review, checkpoint, sync-memory)

## Stage 5 — Report

Print summary:
- Files created
- Rules copied (list)
- Hooks registered (list)
- Next steps: fill in CLAUDE.md, add project goals to memory/project/context.md

## Hard gates

- If `.claude/settings.json` already exists → warn and ask before overwriting
- If `CLAUDE.md` already exists with non-template content → append a "## Harness" section instead of overwriting
