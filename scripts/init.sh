#!/usr/bin/env bash
# init.sh — Scan src/ and generate .claude/ harness for any project
# Usage: ./init.sh [project-dir]
#
# What it does:
#   1. Detect tech stack from manifests + src/ scan
#   2. Copy appropriate rules, skills, hooks into .claude/
#   3. Write .claude/settings.json with hooks registered
#   4. Bootstrap memory system at .claude/memory/
#   5. Generate project-specific CLAUDE.md

set -euo pipefail

HARNESS_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="${1:-$(pwd)}"
CLAUDE_DIR="$PROJECT_DIR/.claude"
GIT_USER="$(git -C "$PROJECT_DIR" config user.name 2>/dev/null || echo "unknown")"
GIT_EMAIL="$(git -C "$PROJECT_DIR" config user.email 2>/dev/null || echo "")"
PROJECT_NAME="$(basename "$PROJECT_DIR")"

echo "🔍 Scanning project: $PROJECT_NAME"
echo "   Dir: $PROJECT_DIR"
echo ""

# ─── Tech Stack Detection ────────────────────────────────────────────────────

SIGNALS=()

detect_stack() {
  # Node.js / JavaScript / TypeScript
  if [ -f "$PROJECT_DIR/package.json" ]; then
    SIGNALS+=("nodejs")
    local pkg="$PROJECT_DIR/package.json"

    grep -q '"typescript"'          "$pkg" 2>/dev/null && SIGNALS+=("typescript")
    [ -f "$PROJECT_DIR/tsconfig.json" ]                && SIGNALS+=("typescript")
    grep -q '"next"'                "$pkg" 2>/dev/null && SIGNALS+=("nextjs")
    grep -q '"react"'               "$pkg" 2>/dev/null && SIGNALS+=("react")
    grep -q '"express"'             "$pkg" 2>/dev/null && SIGNALS+=("express")
    grep -q '"fastify"'             "$pkg" 2>/dev/null && SIGNALS+=("fastify")
    grep -q '"@nestjs/core"'        "$pkg" 2>/dev/null && SIGNALS+=("nestjs")
    grep -q '"prisma"'              "$pkg" 2>/dev/null && SIGNALS+=("prisma")
    grep -q '"mongoose"'            "$pkg" 2>/dev/null && SIGNALS+=("mongodb")
    grep -q '"@langchain/core"'     "$pkg" 2>/dev/null && SIGNALS+=("langchain")
    grep -q '"@langchain/langgraph"' "$pkg" 2>/dev/null && SIGNALS+=("langgraph")
    grep -q '"@copilotkit'          "$pkg" 2>/dev/null && SIGNALS+=("copilotkit")
    grep -q '"openai"'              "$pkg" 2>/dev/null && SIGNALS+=("openai")
    grep -q '"@anthropic-ai'        "$pkg" 2>/dev/null && SIGNALS+=("anthropic")
    grep -q '"graphql"'             "$pkg" 2>/dev/null && SIGNALS+=("graphql")
    grep -q '"trpc"'                "$pkg" 2>/dev/null && SIGNALS+=("trpc")
    grep -q '"vitest"'              "$pkg" 2>/dev/null && SIGNALS+=("vitest")
    grep -q '"jest"'                "$pkg" 2>/dev/null && SIGNALS+=("jest")
    grep -q '"playwright"'          "$pkg" 2>/dev/null && SIGNALS+=("playwright")
    [ -f "$PROJECT_DIR/pnpm-lock.yaml" ]               && SIGNALS+=("pnpm")
    [ -f "$PROJECT_DIR/yarn.lock" ]                    && SIGNALS+=("yarn")
  fi

  # Python
  if [ -f "$PROJECT_DIR/requirements.txt" ] || [ -f "$PROJECT_DIR/pyproject.toml" ] || [ -f "$PROJECT_DIR/setup.py" ]; then
    SIGNALS+=("python")
    local req="${PROJECT_DIR}/requirements.txt"
    local pyp="${PROJECT_DIR}/pyproject.toml"

    grep -qi "fastapi"      "$req" "$pyp" 2>/dev/null && SIGNALS+=("fastapi")
    grep -qi "django"       "$req" "$pyp" 2>/dev/null && SIGNALS+=("django")
    grep -qi "flask"        "$req" "$pyp" 2>/dev/null && SIGNALS+=("flask")
    grep -qi "langchain"    "$req" "$pyp" 2>/dev/null && SIGNALS+=("langchain")
    grep -qi "langgraph"    "$req" "$pyp" 2>/dev/null && SIGNALS+=("langgraph")
    grep -qi "sqlalchemy"   "$req" "$pyp" 2>/dev/null && SIGNALS+=("sqlalchemy")
    grep -qi "anthropic"    "$req" "$pyp" 2>/dev/null && SIGNALS+=("anthropic")
    grep -qi "openai"       "$req" "$pyp" 2>/dev/null && SIGNALS+=("openai")
    grep -qi "pytest"       "$req" "$pyp" 2>/dev/null && SIGNALS+=("pytest")
    [ -f "$PROJECT_DIR/.ruff.toml" ] || grep -qi "ruff" "$pyp" 2>/dev/null && SIGNALS+=("ruff")
  fi

  # Go
  [ -f "$PROJECT_DIR/go.mod" ] && SIGNALS+=("golang")

  # Java / Kotlin
  [ -f "$PROJECT_DIR/pom.xml" ]       && SIGNALS+=("java") && SIGNALS+=("maven")
  [ -f "$PROJECT_DIR/build.gradle" ]  && SIGNALS+=("java") && SIGNALS+=("gradle")
  [ -f "$PROJECT_DIR/build.gradle.kts" ] && SIGNALS+=("kotlin") && SIGNALS+=("gradle")

  # Rust
  [ -f "$PROJECT_DIR/Cargo.toml" ] && SIGNALS+=("rust")

  # Docker
  [ -f "$PROJECT_DIR/Dockerfile" ] || [ -f "$PROJECT_DIR/docker-compose.yml" ] && SIGNALS+=("docker")

  # Database hints from src scan
  if [ -d "$PROJECT_DIR/src" ]; then
    grep -rq "prisma\|@prisma"   "$PROJECT_DIR/src" 2>/dev/null && has_signal "prisma"  || true
    grep -rq "mongoose\|mongodb" "$PROJECT_DIR/src" 2>/dev/null && SIGNALS+=("mongodb") || true
    grep -rq "postgres\|pg\b"    "$PROJECT_DIR/src" 2>/dev/null && SIGNALS+=("postgres") || true
    grep -rq "redis"             "$PROJECT_DIR/src" 2>/dev/null && SIGNALS+=("redis")   || true
    grep -rq "lancedb"           "$PROJECT_DIR/src" 2>/dev/null && SIGNALS+=("lancedb") || true
  fi
}

has_signal() {
  local needle="$1"
  for s in "${SIGNALS[@]}"; do [[ "$s" == "$needle" ]] && return 0; done
  return 1
}

detect_stack

# Deduplicate
SIGNALS=($(printf '%s\n' "${SIGNALS[@]}" | sort -u))

echo "📦 Detected signals:"
printf '   %s\n' "${SIGNALS[@]}"
echo ""

# ─── Create .claude/ structure ───────────────────────────────────────────────

mkdir -p "$CLAUDE_DIR"/{rules,skills,hooks,memory/{feedback,project,commits,sessions},specs}

# ─── Copy Universal Rules ────────────────────────────────────────────────────

echo "📋 Copying rules..."
cp "$HARNESS_DIR/rules/git.md"            "$CLAUDE_DIR/rules/git.md"
cp "$HARNESS_DIR/rules/testing.md"        "$CLAUDE_DIR/rules/testing.md"
cp "$HARNESS_DIR/rules/orchestration.md"  "$CLAUDE_DIR/rules/orchestration.md"
cp "$HARNESS_DIR/rules/memory.md"         "$CLAUDE_DIR/rules/memory.md"

# Stack-specific rules
has_signal "typescript" && cp "$HARNESS_DIR/rules/stacks/typescript.md"  "$CLAUDE_DIR/rules/typescript.md"  2>/dev/null || true
has_signal "nodejs"     && cp "$HARNESS_DIR/rules/stacks/javascript.md"  "$CLAUDE_DIR/rules/javascript.md"  2>/dev/null || true
has_signal "react"      && cp "$HARNESS_DIR/rules/stacks/react.md"       "$CLAUDE_DIR/rules/react.md"       2>/dev/null || true
has_signal "jest"       && cp "$HARNESS_DIR/rules/stacks/jest.md"        "$CLAUDE_DIR/rules/jest.md"        2>/dev/null || true
has_signal "python"     && cp "$HARNESS_DIR/rules/stacks/python.md"      "$CLAUDE_DIR/rules/python.md"      2>/dev/null || true
has_signal "langgraph"  && cp "$HARNESS_DIR/rules/stacks/langgraph.md"   "$CLAUDE_DIR/rules/langgraph.md"   2>/dev/null || true
has_signal "nextjs"     && cp "$HARNESS_DIR/rules/stacks/nextjs.md"      "$CLAUDE_DIR/rules/nextjs.md"      2>/dev/null || true
has_signal "prisma"     && cp "$HARNESS_DIR/rules/stacks/prisma.md"      "$CLAUDE_DIR/rules/prisma.md"      2>/dev/null || true
has_signal "fastapi"    && cp "$HARNESS_DIR/rules/stacks/fastapi.md"     "$CLAUDE_DIR/rules/fastapi.md"     2>/dev/null || true

# ─── Copy Universal Skills ───────────────────────────────────────────────────

echo "🛠  Copying skills..."
mkdir -p "$CLAUDE_DIR/skills"
for skill in coordinator feature fix-bug code-review checkpoint sync-memory brainstorming grill writing-plans blast-radius; do
  if [ -d "$HARNESS_DIR/skills/$skill" ]; then
    cp -r "$HARNESS_DIR/skills/$skill" "$CLAUDE_DIR/skills/"
  fi
done

# ─── Copy Agents ─────────────────────────────────────────────────────────────

echo "🤖  Copying agents..."
mkdir -p "$CLAUDE_DIR/agents"
if [ -d "$HARNESS_DIR/agents" ]; then
  cp "$HARNESS_DIR/agents/"*.md "$CLAUDE_DIR/agents/" 2>/dev/null || true
fi

# ─── Copy Templates ───────────────────────────────────────────────────────────

echo "📄  Copying templates..."
mkdir -p "$CLAUDE_DIR/templates"
if [ -d "$HARNESS_DIR/templates" ]; then
  cp "$HARNESS_DIR/templates/"*.md   "$CLAUDE_DIR/templates/" 2>/dev/null || true
  cp "$HARNESS_DIR/templates/"*.json "$CLAUDE_DIR/templates/" 2>/dev/null || true
fi

# ─── Copy Hooks ──────────────────────────────────────────────────────────────

echo "🪝  Copying hooks..."
cp "$HARNESS_DIR/hooks/commit-quality-gate.sh"  "$CLAUDE_DIR/hooks/"
cp "$HARNESS_DIR/hooks/branch-guard.sh"         "$CLAUDE_DIR/hooks/"
cp "$HARNESS_DIR/hooks/state-breadcrumb.sh"     "$CLAUDE_DIR/hooks/"
cp "$HARNESS_DIR/hooks/scope-gate.sh"           "$CLAUDE_DIR/hooks/"
cp "$HARNESS_DIR/hooks/save-commit-memory.sh"   "$CLAUDE_DIR/hooks/"

# Python: add ruff hook
has_signal "python" && cp "$HARNESS_DIR/hooks/stacks/ruff-on-edit.sh" "$CLAUDE_DIR/hooks/" 2>/dev/null || true
# JS/TS: add eslint hook
has_signal "typescript" && cp "$HARNESS_DIR/hooks/stacks/eslint-on-edit.sh" "$CLAUDE_DIR/hooks/" 2>/dev/null || true

chmod +x "$CLAUDE_DIR/hooks/"*.sh 2>/dev/null || true

# ─── Generate settings.json ──────────────────────────────────────────────────

echo "⚙️  Writing .claude/settings.json..."

EXTRA_HOOKS=""
has_signal "python"     && EXTRA_HOOKS+=',
      { "matcher": "Edit", "hooks": [{ "type": "command", "command": ".claude/hooks/ruff-on-edit.sh" }] }' || true
has_signal "typescript" && EXTRA_HOOKS+=',
      { "matcher": "Edit", "hooks": [{ "type": "command", "command": ".claude/hooks/eslint-on-edit.sh" }] }' || true

cat > "$CLAUDE_DIR/settings.json" << SETTINGS
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Agent",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/agent-progress.sh pre",
            "statusMessage": "🤖 Spawning agent..."
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"\$CLAUDE_TOOL_INPUT\" | grep -q 'git commit' && .claude/hooks/commit-quality-gate.sh || true"
          },
          {
            "type": "command",
            "command": "echo \"\$CLAUDE_TOOL_INPUT\" | grep -q 'git push' && .claude/hooks/branch-guard.sh || true"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Agent",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/agent-progress.sh",
            "statusMessage": "✅ Agent completed"
          }
        ]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/agent-progress.sh",
            "statusMessage": "📝 Logging edit..."
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/agent-progress.sh",
            "statusMessage": "💻 Logging command..."
          },
          {
            "type": "command",
            "command": "echo \"\$CLAUDE_TOOL_INPUT\" | grep -q 'git commit' && .claude/hooks/save-commit-memory.sh || true"
          }
        ]
      }${EXTRA_HOOKS}
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/scope-gate.sh"
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/state-breadcrumb.sh"
          }
        ]
      }
    ]
  },
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Bash(npm *)",
      "Bash(pnpm *)",
      "Bash(npx *)",
      "Bash(find *)",
      "Bash(grep *)",
      "Bash(ls *)"
    ]
  }
}
SETTINGS

# ─── Bootstrap Memory ────────────────────────────────────────────────────────

echo "🧠  Bootstrapping memory..."
cp "$HARNESS_DIR/memory/MEMORY.md.template"         "$CLAUDE_DIR/memory/MEMORY.md"
cp "$HARNESS_DIR/memory/templates/project.md"       "$CLAUDE_DIR/memory/project/context.md"
cp "$HARNESS_DIR/memory/templates/user.md"          "$CLAUDE_DIR/memory/user.md"

# Stamp the project context
sed -i '' "s/{{PROJECT_NAME}}/$PROJECT_NAME/g"  "$CLAUDE_DIR/memory/MEMORY.md" 2>/dev/null || \
  sed -i   "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" "$CLAUDE_DIR/memory/MEMORY.md"

sed -i '' "s/{{GIT_USER}}/$GIT_USER/g"   "$CLAUDE_DIR/memory/user.md" 2>/dev/null || \
  sed -i   "s/{{GIT_USER}}/$GIT_USER/g"  "$CLAUDE_DIR/memory/user.md"
sed -i '' "s/{{GIT_EMAIL}}/$GIT_EMAIL/g" "$CLAUDE_DIR/memory/user.md" 2>/dev/null || \
  sed -i   "s/{{GIT_EMAIL}}/$GIT_EMAIL/g" "$CLAUDE_DIR/memory/user.md"

# ─── Generate project CLAUDE.md ──────────────────────────────────────────────

echo "📝  Generating CLAUDE.md..."
STACK_LIST=$(printf '%s, ' "${SIGNALS[@]}" | sed 's/, $//')

# ── Extract scripts from package.json ────────────────────────────────────────
PKG_SCRIPTS=""
if [ -f "$PROJECT_DIR/package.json" ] && command -v python3 &>/dev/null; then
  PKG_SCRIPTS=$(python3 - "$PROJECT_DIR/package.json" <<'PYEOF'
import json, sys
try:
  pkg = json.load(open(sys.argv[1]))
  scripts = pkg.get("scripts", {})
  pm = "pnpm" if open(sys.argv[1]).read().find('"pnpm') >= 0 else "npm"
  lines = []
  priority = ["dev", "start", "build", "test", "lint", "typecheck", "check-types", "e2e", "eval"]
  shown = set()
  for key in priority:
    if key in scripts:
      lines.append(f"{pm} {key}")
      shown.add(key)
  for key, val in scripts.items():
    if key not in shown and not key.startswith("post") and not key.startswith("pre"):
      lines.append(f"{pm} {key}")
  print("\n".join(f"# {l}" if i > 4 else l for i, l in enumerate(lines)))
except Exception as e:
  print("# (could not parse package.json scripts)")
PYEOF
)
fi

# ── Detect key directories ────────────────────────────────────────────────────
detect_dirs() {
  local dirs=()
  [ -d "$PROJECT_DIR/src" ]        && dirs+=("src/")
  [ -d "$PROJECT_DIR/app" ]        && dirs+=("app/")
  [ -d "$PROJECT_DIR/apps" ]       && dirs+=("apps/")
  [ -d "$PROJECT_DIR/packages" ]   && dirs+=("packages/")
  [ -d "$PROJECT_DIR/lib" ]        && dirs+=("lib/")
  [ -d "$PROJECT_DIR/server" ]     && dirs+=("server/")
  [ -d "$PROJECT_DIR/api" ]        && dirs+=("api/")
  [ -d "$PROJECT_DIR/components" ] && dirs+=("components/")
  [ -d "$PROJECT_DIR/hooks" ]      && dirs+=("hooks/")
  [ -d "$PROJECT_DIR/utils" ]      && dirs+=("utils/")
  [ -d "$PROJECT_DIR/tests" ]      && dirs+=("tests/")
  [ -d "$PROJECT_DIR/e2e" ]        && dirs+=("e2e/")
  [ -d "$PROJECT_DIR/docs" ]       && dirs+=("docs/")
  [ -d "$PROJECT_DIR/scripts" ]    && dirs+=("scripts/")
  printf '%s\n' "${dirs[@]}"
}

dir_label() {
  case "$1" in
    "src/")        echo "Source code" ;;
    "app/")        echo "Next.js App Router pages and layouts" ;;
    "apps/")       echo "Monorepo app packages" ;;
    "packages/")   echo "Shared library packages" ;;
    "lib/")        echo "Shared utilities and clients" ;;
    "server/")     echo "Server-side code and DB" ;;
    "api/")        echo "API handlers" ;;
    "components/") echo "React UI components" ;;
    "hooks/")      echo "React hooks" ;;
    "utils/")      echo "Utility functions" ;;
    "tests/")      echo "Test files" ;;
    "e2e/")        echo "End-to-end tests (Playwright)" ;;
    "docs/")       echo "Documentation" ;;
    "scripts/")    echo "Build and utility scripts" ;;
    *)             echo "<!-- purpose -->" ;;
  esac
}

DIR_ROWS=""
while IFS= read -r dir; do
  [ -z "$dir" ] && continue
  label=$(dir_label "$dir")
  DIR_ROWS="${DIR_ROWS}| \`${dir}\` | ${label} |
"
done < <(detect_dirs)

# ── Detect test commands ──────────────────────────────────────────────────────
TEST_CMD="${PM:-npm} test"
has_signal "vitest"     && TEST_CMD="pnpm test          # vitest"
has_signal "jest"       && TEST_CMD="pnpm test          # jest"
has_signal "pytest"     && TEST_CMD="pytest"
E2E_CMD=""
has_signal "playwright" && E2E_CMD="pnpm test:e2e       # playwright"

# ── Package manager ───────────────────────────────────────────────────────────
PM="npm"
has_signal "pnpm" && PM="pnpm"
has_signal "yarn" && PM="yarn"

# ── Monorepo note ─────────────────────────────────────────────────────────────
MONO_NOTE=""
( [ -f "$PROJECT_DIR/pnpm-workspace.yaml" ] || [ -f "$PROJECT_DIR/turbo.json" ] ) && \
  MONO_NOTE="# Monorepo — filter by workspace: ${PM} --filter <workspace> <cmd>"

# ── Lint / typecheck commands ─────────────────────────────────────────────────
LINT_CMD="${PM} lint"
has_signal "python"     && LINT_CMD="ruff check ."
TYPECHECK_CMD="${PM} build"
has_signal "python"     && TYPECHECK_CMD="mypy ."
# prefer check-types / typecheck script if it exists
if has_signal "typescript" && [ -f "$PROJECT_DIR/package.json" ]; then
  grep -q '"check-types"' "$PROJECT_DIR/package.json" 2>/dev/null && TYPECHECK_CMD="${PM} check-types"
  grep -q '"typecheck"'   "$PROJECT_DIR/package.json" 2>/dev/null && TYPECHECK_CMD="${PM} typecheck"
fi

# ── Stack-specific constraints ────────────────────────────────────────────────
CONSTRAINTS=""
has_signal "pnpm"       && CONSTRAINTS="${CONSTRAINTS}- \`pnpm\` only — never npm/yarn
"
has_signal "typescript" && CONSTRAINTS="${CONSTRAINTS}- TypeScript strict — \`unknown\` over \`any\`, explicit return types on exports
"
has_signal "nextjs"     && CONSTRAINTS="${CONSTRAINTS}- Next.js App Router — server components by default; \`\"use client\"\` only when needed
"
has_signal "langgraph"  && CONSTRAINTS="${CONSTRAINTS}- LangGraph state: mutate only via node return values, never direct mutation
"
has_signal "prisma"     && CONSTRAINTS="${CONSTRAINTS}- Never raw SQL — always use Prisma client; migrations via \`prisma migrate dev\`
"
has_signal "python"     && CONSTRAINTS="${CONSTRAINTS}- Always activate virtualenv first; never \`pip install\` globally
"
[ -z "$CONSTRAINTS" ] && CONSTRAINTS="<!-- Add project-specific constraints here -->
"

cat > "$PROJECT_DIR/CLAUDE.md" << CLAUDEMD
# CLAUDE.md

## Auto-Coordinator (applies to every prompt)

**You ARE the coordinator by default.**

**\`TaskCreate\` is mandatory — literal first tool call, before any Read/Bash/Glob.**

### Step 1 — Classify intent from prompt text

| Intent     | Prompt signals                                        | Pipeline                                         |
| ---------- | ----------------------------------------------------- | ------------------------------------------------ |
| \`feat\`     | implement, add, create, build, new feature            | pm → architect → developer → reviewer → qa       |
| \`fix\`      | fix, bug, broken, error, crash, not working, failing  | pm (root-cause only) → developer → reviewer → qa |
| \`refactor\` | refactor, clean up, simplify, reorganize, restructure | architect → developer → reviewer → qa            |
| \`review\`   | review, audit, check, feedback on, look at            | reviewer only                                    |
| \`chore\`    | update dependency, upgrade, bump, config, tooling     | developer → qa                                   |
| \`test\`     | write test, add test, coverage, test for              | developer (haiku) → qa                           |
| \`explain\`  | explain, how does, what is, why, walk me through      | conversational — no agents                       |

### Step 2 — Classify lane

| Lane        | When                                  | Effect on pipeline                                               |
| ----------- | ------------------------------------- | ---------------------------------------------------------------- |
| \`tiny\`      | 0–1 risk flags, single file, < 30 min | May collapse to single agent; skip routing summary               |
| \`normal\`    | 2–3 risk flags                        | Run pipeline as-is; show routing line                            |
| \`high-risk\` | 4+ flags or hard gate                 | Always full pipeline: pm → architect → developer → reviewer → qa |

**Hard gates** (always \`high-risk\`): \`auth · authz · data-loss · migration · security · external provider · public contract\`

### Step 3 — Dispatch

1. **Create \`TaskCreate\` entries for every step** before any work
2. Mark \`in_progress\` before each step, \`completed\` immediately after
3. Load \`.claude/docs/\` + \`.claude/docs/solutions/INDEX.md\`
4. For \`normal\`/\`high-risk\`: show \`Intent: <type> · Lane: <lane> · Pipeline: <agents>\`
5. Run agents with wave-based parallel execution (\`run_in_background: true\`)

**Wave model**: \`haiku\` for tests/types/constants; \`sonnet\` for complex logic
**Pure conversational** (no tool use) → answer directly, no tasks needed

---

## Session Resume (read this FIRST, every session)

\`\`\`bash
cat specs/HANDOFF.md 2>/dev/null && rm -f specs/HANDOFF.md
cat .claude/docs/solutions/INDEX.md 2>/dev/null
grep -rl "decision: pending" specs/ 2>/dev/null
\`\`\`

If \`specs/HANDOFF.md\` exists → read fully → continue from "Next steps" → delete it.
Run \`/compact\` before ending a session. Run \`/compound\` after significant debugging.

---

## Agent Context

**All agents MUST read \`.claude/docs/index.md\` before scanning any source file.**

| Doc | Contents |
|-----|----------|
| \`.claude/docs/architecture.md\`  | Layers, data flow, key decisions |
| \`.claude/docs/conventions.md\`   | Naming, imports, anti-patterns |
| \`.claude/docs/stack.md\`         | Tech stack, run commands, test commands |
| \`.claude/docs/entry-points.md\`  | API routes, jobs, CLI commands |
| \`.claude/docs/test-strategy.md\` | Test structure, markers, conventions |

If \`.claude/docs/\` does not exist → run \`/project-init\` first.

---

## Project Overview

**Stack:** ${STACK_LIST}

### Key directories

| Path | Purpose |
|------|---------|
${DIR_ROWS}
## Multi-Agent Ticket Workflow

For any non-trivial task, use \`/ticket #<issue> <description>\` to run the full pipeline:

| Phase | Agent             | Role                                       |
| ----- | ----------------- | ------------------------------------------ |
| 1     | \`pm-agent\`        | Research requirements & codebase context   |
| 2     | \`architect-agent\` | Technical design & implementation plan     |
| 3     | \`developer-agent\` | Implement the plan                         |
| 4     | \`reviewer-agent\`  | Code review — APPROVED or CHANGES REQUIRED |
| 5     | \`qa-agent\`        | Run checks, fix surface errors, commit     |

For lightweight tasks (small fix, chore), use \`/task\` instead.

## Lightweight Task Workflow

### Step 1 — Break down & track
Use \`TaskCreate\` before writing any code. Mark \`in_progress\` when starting, \`completed\` when done.

### Step 2 — Implement
Edit existing files over creating new ones. No comments unless the WHY is non-obvious.

### Step 3 — Verify

\`\`\`bash
${LINT_CMD}
${TYPECHECK_CMD}
${TEST_CMD}
${E2E_CMD}
\`\`\`

### Step 4 — Commit

\`\`\`
<type>: <description>
\`\`\`

Types: \`feat\` \`fix\` \`refactor\` \`chore\` \`docs\` \`test\`

## Common Commands

\`\`\`bash
${PKG_SCRIPTS:-# Fill in run commands}
${MONO_NOTE}
\`\`\`

## Key Rules

- Keep CLAUDE.md under 200 lines
${CONSTRAINTS}
CLAUDEMD

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo "✅  Harness initialized for: $PROJECT_NAME"
echo ""
echo "   .claude/"
echo "   ├── rules/         $(ls "$CLAUDE_DIR/rules/" | wc -l | tr -d ' ') files"
echo "   ├── skills/        $(ls "$CLAUDE_DIR/skills/" | wc -l | tr -d ' ') skills"
echo "   ├── hooks/         $(ls "$CLAUDE_DIR/hooks/" | wc -l | tr -d ' ') scripts"
echo "   ├── agents/        $(ls "$CLAUDE_DIR/agents/" 2>/dev/null | wc -l | tr -d ' ') agents"
echo "   ├── templates/     $(ls "$CLAUDE_DIR/templates/" 2>/dev/null | wc -l | tr -d ' ') templates"
echo "   ├── memory/        bootstrapped"
echo "   └── settings.json  hooks registered"
echo ""
echo "Next steps:"
echo "  1. Edit CLAUDE.md — fill in run commands, architecture, constraints"
echo "  2. Edit .claude/memory/project/context.md — add project goals"
echo "  3. Edit .claude/memory/user.md — add your role / preferences"
echo ""
