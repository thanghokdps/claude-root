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
for skill in feature fix-bug code-review checkpoint sync-memory; do
  if [ -d "$HARNESS_DIR/skills/$skill" ]; then
    cp -r "$HARNESS_DIR/skills/$skill" "$CLAUDE_DIR/skills/"
  fi
done

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
has_signal "python"     && EXTRA_HOOKS+='
      { "matcher": "Edit", "hooks": [{ "type": "command", "command": ".claude/hooks/ruff-on-edit.sh" }] },' || true
has_signal "typescript" && EXTRA_HOOKS+='
      { "matcher": "Edit", "hooks": [{ "type": "command", "command": ".claude/hooks/eslint-on-edit.sh" }] },' || true

cat > "$CLAUDE_DIR/settings.json" << SETTINGS
{
  "hooks": {
    "PreToolUse": [
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
        "matcher": "Bash",
        "hooks": [
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

cat > "$PROJECT_DIR/CLAUDE.md" << CLAUDEMD
# ${PROJECT_NAME} — Claude Code Guide

> Auto-generated by harness init on $(date +%Y-%m-%d). Edit to add project specifics.

## Stack detected

**${STACK_LIST}**

## Run the project

\`\`\`bash
# Fill in your actual run commands here
\`\`\`

## Architecture

\`\`\`
# Describe your project structure here after init
\`\`\`

## Key directories

| Path | Purpose |
|------|---------|
| \`src/\` | Main source |

## Available skills

| Skill | Command | Purpose |
|-------|---------|---------|
| feature | \`/feature <description>\` | Intake → plan → build → review |
| fix-bug | \`/fix-bug <symptom>\` | Root cause → fix → verify → commit |
| code-review | \`/code-review [low\|medium\|high]\` | Review diff |
| checkpoint | \`/checkpoint\` | Progress vs plan + quality gates |
| sync-memory | \`/sync-memory\` | Pull latest + rebuild memory from your commits |

## Constraints

<!-- Add project-specific constraints here -->
CLAUDEMD

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo "✅  Harness initialized for: $PROJECT_NAME"
echo ""
echo "   .claude/"
echo "   ├── rules/         $(ls "$CLAUDE_DIR/rules/" | wc -l | tr -d ' ') files"
echo "   ├── skills/        $(ls "$CLAUDE_DIR/skills/" | wc -l | tr -d ' ') skills"
echo "   ├── hooks/         $(ls "$CLAUDE_DIR/hooks/" | wc -l | tr -d ' ') scripts"
echo "   ├── memory/        bootstrapped"
echo "   └── settings.json  hooks registered"
echo ""
echo "Next steps:"
echo "  1. Edit CLAUDE.md — fill in run commands, architecture, constraints"
echo "  2. Edit .claude/memory/project/context.md — add project goals"
echo "  3. Edit .claude/memory/user.md — add your role / preferences"
echo ""
