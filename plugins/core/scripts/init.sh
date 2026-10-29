#!/usr/bin/env bash
# init.sh — Scan src/ and generate .claude/ harness for any project
# Usage: ./init.sh [project-dir]            — lean: shared skills/rules/hooks come from the kit plugins
#        STANDALONE=1 ./init.sh [project-dir] — also copy shared rules/skills/commands/agents/hooks into .claude/
#                                             (for repos shared with people who do not have the plugin)
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
STANDALONE="${STANDALONE:-0}"

# Sibling role plugin dir: plugins/<name> in a kit checkout, cache/<marketplace>/<name>/<version> once installed.
plugin_dir() {
  if [ -d "$HARNESS_DIR/../$1/.claude-plugin" ]; then (cd "$HARNESS_DIR/../$1" && pwd); return; fi
  local v
  v="$(ls -d "$HARNESS_DIR/../../$1"/*/ 2>/dev/null | sort -V | tail -1 || true)"
  if [ -n "$v" ]; then (cd "$v" && pwd); fi
}

echo "🔍 Scanning project: $PROJECT_NAME"
echo "   Dir: $PROJECT_DIR"
echo ""

# ─── Tech Stack Detection ────────────────────────────────────────────────────

SIGNALS=()

detect_stack() {
  # Node.js / JavaScript / TypeScript
  if [ -f "$PROJECT_DIR/package.json" ]; then
    SIGNALS+=("nodejs")
    # Workspace manifests too: a monorepo declares its deps in apps/*, packages/*, … not the root.
    local pkg=()
    while IFS= read -r f; do pkg+=("$f"); done < <(find "$PROJECT_DIR" -maxdepth 3 -name package.json -not -path '*/node_modules/*')

    grep -q '"typescript"'          "${pkg[@]}" 2>/dev/null && SIGNALS+=("typescript")
    [ -f "$PROJECT_DIR/tsconfig.json" ]                && SIGNALS+=("typescript")
    grep -q '"next"'                "${pkg[@]}" 2>/dev/null && SIGNALS+=("nextjs")
    grep -q '"react"'               "${pkg[@]}" 2>/dev/null && SIGNALS+=("react")
    grep -q '"express"'             "${pkg[@]}" 2>/dev/null && SIGNALS+=("express")
    grep -q '"fastify"'             "${pkg[@]}" 2>/dev/null && SIGNALS+=("fastify")
    grep -q '"@nestjs/core"'        "${pkg[@]}" 2>/dev/null && SIGNALS+=("nestjs")
    grep -q '"prisma"'              "${pkg[@]}" 2>/dev/null && SIGNALS+=("prisma")
    grep -q '"mongoose"'            "${pkg[@]}" 2>/dev/null && SIGNALS+=("mongodb")
    grep -q '"@langchain/core"'     "${pkg[@]}" 2>/dev/null && SIGNALS+=("langchain")
    grep -q '"@langchain/langgraph"' "${pkg[@]}" 2>/dev/null && SIGNALS+=("langgraph")
    grep -q '"@copilotkit'          "${pkg[@]}" 2>/dev/null && SIGNALS+=("copilotkit")
    grep -q '"openai"'              "${pkg[@]}" 2>/dev/null && SIGNALS+=("openai")
    grep -q '"@anthropic-ai'        "${pkg[@]}" 2>/dev/null && SIGNALS+=("anthropic")
    grep -q '"graphql"'             "${pkg[@]}" 2>/dev/null && SIGNALS+=("graphql")
    grep -q '"trpc"'                "${pkg[@]}" 2>/dev/null && SIGNALS+=("trpc")
    grep -q '"vitest"'              "${pkg[@]}" 2>/dev/null && SIGNALS+=("vitest")
    grep -q '"jest"'                "${pkg[@]}" 2>/dev/null && SIGNALS+=("jest")
    grep -q '"playwright"'          "${pkg[@]}" 2>/dev/null && SIGNALS+=("playwright")
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
  [ ${#SIGNALS[@]} -eq 0 ] && return 1
  for s in "${SIGNALS[@]}"; do [[ "$s" == "$needle" ]] && return 0; done
  return 1
}

detect_stack

# Deduplicate. bash 3.2 (macOS default) expands "${arr[@]}" on an empty array as an
# unbound variable under `set -u`, so a project with no recognised manifest would abort here.
if [ ${#SIGNALS[@]} -gt 0 ]; then
  SIGNALS=($(printf '%s\n' "${SIGNALS[@]}" | sort -u))
  echo "📦 Detected signals:"
  printf '   %s\n' "${SIGNALS[@]}"
else
  echo "📦 No stack signals detected — installing universal rules and hooks only."
fi
echo ""

# ─── Create .claude/ structure ───────────────────────────────────────────────

# specs/ lives at the project root, not under .claude/ — session-handoff.sh and every
# skill write to $REPO_DIR/specs. Creating .claude/specs here left an empty folder forever.
mkdir -p "$CLAUDE_DIR"/{rules,skills,hooks,memory/{feedback,project,commits,sessions}}
mkdir -p "$PROJECT_DIR/specs"

# ─── Copy Universal Rules ────────────────────────────────────────────────────

echo "📋 Copying rules..."
# Copy every universal rule. A hardcoded list here had drifted to 4 of 13 — agent-principles.md,
# security.md, code-quality.md and plan-format.md never reached a project despite being
# referenced as mandatory. Stack rules under rules/stacks/ stay conditional, below.
# Lean mode skips them: ~/.claude/rules already loads them, and a second copy loads twice.
if [ "$STANDALONE" = 1 ]; then
  for rule in "$HARNESS_DIR"/rules/*.md; do
    [ -f "$rule" ] && cp "$rule" "$CLAUDE_DIR/rules/"
  done
fi

# Stack-specific rules
has_signal "typescript" && cp "$HARNESS_DIR/rules/stacks/typescript.md"  "$CLAUDE_DIR/rules/typescript.md"  2>/dev/null || true
has_signal "nodejs"     && cp "$HARNESS_DIR/rules/stacks/javascript.md"  "$CLAUDE_DIR/rules/javascript.md"  2>/dev/null || true
has_signal "react"      && cp "$HARNESS_DIR/rules/stacks/react.md"       "$CLAUDE_DIR/rules/react.md"       2>/dev/null || true
has_signal "jest"       && cp "$HARNESS_DIR/rules/stacks/jest.md"        "$CLAUDE_DIR/rules/jest.md"        2>/dev/null || true
has_signal "python"     && cp "$HARNESS_DIR/rules/stacks/python.md"      "$CLAUDE_DIR/rules/python.md"      2>/dev/null || true
has_signal "nextjs"     && cp "$HARNESS_DIR/rules/stacks/nextjs.md"      "$CLAUDE_DIR/rules/nextjs.md"      2>/dev/null || true
has_signal "prisma"     && cp "$HARNESS_DIR/rules/stacks/prisma.md"      "$CLAUDE_DIR/rules/prisma.md"      2>/dev/null || true
has_signal "fastapi"    && cp "$HARNESS_DIR/rules/stacks/fastapi.md"     "$CLAUDE_DIR/rules/fastapi.md"     2>/dev/null || true

if [ "$STANDALONE" = 1 ]; then
# ─── Copy Universal Skills ───────────────────────────────────────────────────

echo "🛠  Copying skills..."
mkdir -p "$CLAUDE_DIR/skills"
# Build chain + design chain. The design chain (brainstorming → grill → writing-plans) is what
# turns a rough idea into a PLAN.md before any code is written, so it ships with every project.
for entry in dev/feature dev/fix-bug review/review-checklist dev/checkpoint \
             core/sync-memory plan/brainstorming plan/grill plan/writing-plans \
             plan/domain-model dev/tdd plan/codebase-design review/blast-radius; do
  src="$(plugin_dir "${entry%/*}")/skills/${entry#*/}"
  if [ -d "$src" ]; then
    cp -r "$src" "$CLAUDE_DIR/skills/"
  else
    echo "   ⚠️  ${entry#*/} skipped — plugin ${entry%/*} not found next to core"
  fi
done

# ─── Copy Commands ───────────────────────────────────────────────────────────

echo "⌨️   Copying commands..."
mkdir -p "$CLAUDE_DIR/commands"
for cmd in "$HARNESS_DIR"/templates/project/commands/*.md; do
  [ -f "$cmd" ] && cp "$cmd" "$CLAUDE_DIR/commands/"
done

# ─── Copy Agents ─────────────────────────────────────────────────────────────

echo "🤖  Copying agents..."
mkdir -p "$CLAUDE_DIR/agents"
if [ -d "$HARNESS_DIR/templates/project/agents" ]; then
  cp "$HARNESS_DIR/templates/project/agents/"*.md "$CLAUDE_DIR/agents/" 2>/dev/null || true
fi
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
# Copy every hook in hooks/ — a hardcoded list here silently drifts from the list
# registered in settings.json, which is how agent-progress.sh and session-handoff.sh
# ended up registered but never installed. Stack hooks under hooks/stacks/ stay conditional.
if [ "$STANDALONE" = 1 ]; then
  GUARDS_DIR="$(plugin_dir guards)"
  [ -n "$GUARDS_DIR" ] || echo "   ⚠️  guards not found next to core — shared hooks not copied" >&2
  for hook in "$HARNESS_DIR"/hooks/*.sh "$GUARDS_DIR"/hooks/*.sh; do
    [ -f "$hook" ] && cp "$hook" "$CLAUDE_DIR/hooks/"
  done
fi

# Python: add ruff hook
has_signal "python" && cp "$HARNESS_DIR/hooks/stacks/ruff-on-edit.sh" "$CLAUDE_DIR/hooks/" 2>/dev/null || true
# JS/TS: add eslint hook
has_signal "typescript" && cp "$HARNESS_DIR/hooks/stacks/eslint-on-edit.sh" "$CLAUDE_DIR/hooks/" 2>/dev/null || true

chmod +x "$CLAUDE_DIR/hooks/"*.sh 2>/dev/null || true

# ─── Generate settings.json (rendered from templates/settings.json.template) ──

echo "⚙️  Writing .claude/settings.json..."

SETTINGS_TEMPLATE="$HARNESS_DIR/templates/settings.json.template"
if [ ! -f "$SETTINGS_TEMPLATE" ]; then
  echo "❌ Missing $SETTINGS_TEMPLATE — cannot write settings.json" >&2
  exit 1
fi

# Stack hooks are the only dynamic part; the template carries everything else so the
# registered set and the installed set come from one file.
STACK_HOOKS=""
has_signal "python"     && STACK_HOOKS="$STACK_HOOKS,
      { \"matcher\": \"Edit|Write\", \"hooks\": [{ \"type\": \"command\", \"command\": \"\$CLAUDE_PROJECT_DIR/.claude/hooks/ruff-on-edit.sh\" }] }" || true
has_signal "typescript" && STACK_HOOKS="$STACK_HOOKS,
      { \"matcher\": \"Edit|Write\", \"hooks\": [{ \"type\": \"command\", \"command\": \"\$CLAUDE_PROJECT_DIR/.claude/hooks/eslint-on-edit.sh\" }] }" || true

STANDALONE="$STANDALONE" python3 -I - "$SETTINGS_TEMPLATE" "$CLAUDE_DIR/settings.json" "$STACK_HOOKS" <<'RENDER'
import json, sys
tpl, out, stack = sys.argv[1], sys.argv[2], sys.argv[3]
import os
if os.environ.get("STANDALONE") == "1":
    rendered = open(tpl).read().replace("__STACK_HOOKS__", stack)
else:  # lean: the plugin registers the shared hooks; only stack hooks are project-specific
    rendered = json.dumps({"hooks": {"PostToolUse": json.loads("[" + stack.lstrip(",") + "]")}} if stack.strip() else {}, indent=2)
merged = json.loads(rendered)  # fail loudly on malformed JSON rather than writing it
# Keep what the project already set (enabledPlugins, permissions, env); only `hooks` is ours to write.
if os.path.exists(out):
    existing = json.load(open(out))
    existing.pop("hooks", None)
    merged = {**existing, **merged}
open(out, "w").write(json.dumps(merged, indent=2) + "\n")
RENDER

# ─── Drift guard: every registered hook must exist and be executable ──────────

echo "🔍  Verifying hook wiring..."
MISSING_HOOKS=0
while read -r hook_path; do
  [ -z "$hook_path" ] && continue
  resolved="$PROJECT_DIR/$hook_path"
  if [ ! -f "$resolved" ]; then
    echo "   ❌ registered but not installed: $hook_path" >&2
    MISSING_HOOKS=$((MISSING_HOOKS + 1))
  elif [ ! -x "$resolved" ]; then
    chmod +x "$resolved" 2>/dev/null || true
  fi
done < <(grep -o '\.claude/hooks/[a-z0-9-]*\.sh' "$CLAUDE_DIR/settings.json" | sort -u)

if [ "$MISSING_HOOKS" -gt 0 ]; then
  echo "   ⚠️  $MISSING_HOOKS hook(s) registered in settings.json are missing from .claude/hooks/" >&2
  echo "      Those hook events will fail silently. Add the file to hooks/ or drop it from the template." >&2
else
  echo "   ✅ all registered hooks installed and executable"
fi

# ─── Bootstrap Memory ────────────────────────────────────────────────────────

echo "🧠  Bootstrapping memory..."
cp "$HARNESS_DIR/memory/MEMORY.md.template"         "$CLAUDE_DIR/memory/MEMORY.md"
cp "$HARNESS_DIR/memory/templates/project.md"       "$CLAUDE_DIR/memory/project/context.md"
cp "$HARNESS_DIR/memory/templates/user.md"          "$CLAUDE_DIR/memory/user.md"

# Stamp the project context
MEM_STACK=$( [ ${#SIGNALS[@]} -gt 0 ] && printf '%s, ' "${SIGNALS[@]}" | sed 's/, $//' || echo "none detected")
for f in "$CLAUDE_DIR/memory/MEMORY.md" "$CLAUDE_DIR/memory/project/context.md"; do
  sed -i '' -e "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" -e "s/{{STACK_LIST}}/$MEM_STACK/g" -e "s/{{INIT_DATE}}/$(date +%F)/g" "$f" 2>/dev/null || \
    sed -i -e "s/{{PROJECT_NAME}}/$PROJECT_NAME/g" -e "s/{{STACK_LIST}}/$MEM_STACK/g" -e "s/{{INIT_DATE}}/$(date +%F)/g" "$f"
done

sed -i '' "s/{{GIT_USER}}/$GIT_USER/g"   "$CLAUDE_DIR/memory/user.md" 2>/dev/null || \
  sed -i   "s/{{GIT_USER}}/$GIT_USER/g"  "$CLAUDE_DIR/memory/user.md"
sed -i '' "s/{{GIT_EMAIL}}/$GIT_EMAIL/g" "$CLAUDE_DIR/memory/user.md" 2>/dev/null || \
  sed -i   "s/{{GIT_EMAIL}}/$GIT_EMAIL/g" "$CLAUDE_DIR/memory/user.md"

# user.md holds a name and email: keep it out of the repo (a public repo would publish them).
GITIGNORE="$PROJECT_DIR/.gitignore"
if ! grep -qxF ".claude/memory/user.md" "$GITIGNORE" 2>/dev/null; then
  [ -s "$GITIGNORE" ] && [ -n "$(tail -c1 "$GITIGNORE")" ] && echo >> "$GITIGNORE"
  echo ".claude/memory/user.md" >> "$GITIGNORE"
  echo "   .gitignore: added .claude/memory/user.md (personal, not committed)"
fi

# ─── Generate project CLAUDE.md ──────────────────────────────────────────────

# A re-run must not wipe a CLAUDE.md that /project-init or the team already finalized.
CLAUDE_OUT="$PROJECT_DIR/CLAUDE.md"
if [ -f "$CLAUDE_OUT" ]; then
  echo "📝  CLAUDE.md exists — kept untouched (/project-init Step 8 updates it in place)"
  CLAUDE_OUT=/dev/null
else
  echo "📝  Generating CLAUDE.md..."
fi
if [ ${#SIGNALS[@]} -gt 0 ]; then
  STACK_LIST=$(printf '%s, ' "${SIGNALS[@]}" | sed 's/, $//')
else
  STACK_LIST="none detected"
fi

# ── Extract scripts from package.json ────────────────────────────────────────
PKG_SCRIPTS=""
if [ -f "$PROJECT_DIR/package.json" ] && command -v python3 &>/dev/null; then
  PKG_SCRIPTS=$(python3 -I - "$PROJECT_DIR/package.json" <<'PYEOF'
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
  [ ${#dirs[@]} -gt 0 ] && printf '%s\n' "${dirs[@]}"
  return 0
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

# ── Package manager ───────────────────────────────────────────────────────────
PM="npm"
has_signal "pnpm" && PM="pnpm"
has_signal "yarn" && PM="yarn"

# ── Detect test commands ──────────────────────────────────────────────────────
TEST_CMD="${PM:-npm} test"
has_signal "vitest"     && TEST_CMD="${PM} test          # vitest"
has_signal "jest"       && TEST_CMD="${PM} test          # jest"
has_signal "pytest"     && TEST_CMD="pytest"
E2E_CMD=""
has_signal "playwright" && E2E_CMD="${PM} test:e2e       # playwright"

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

cat > "$CLAUDE_OUT" << CLAUDEMD
# ${PROJECT_NAME}

Coordination (lanes, hard gates, review flow) comes from the global \`~/.claude/CLAUDE.md\` and the kit plugins. This file holds only what is specific to this repo.

## Agent Context

Read \`.claude/docs/index.md\` before scanning source files. If \`.claude/docs/\` is missing, run \`/project-init\`.

| Doc | Contents |
|-----|----------|
| \`.claude/docs/architecture.md\`  | Layers, data flow, key decisions |
| \`.claude/docs/conventions.md\`   | Naming, imports, anti-patterns |
| \`.claude/docs/stack.md\`         | Tech stack, run commands, test commands |
| \`.claude/docs/entry-points.md\`  | API routes, jobs, CLI commands |
| \`.claude/docs/test-strategy.md\` | Test structure, markers, conventions |

## Project Overview

**Stack:** ${STACK_LIST}

| Path | Purpose |
|------|---------|
${DIR_ROWS}
## Verify (in this order)

\`\`\`bash
${TYPECHECK_CMD}
${LINT_CMD}
${TEST_CMD}
${E2E_CMD}
\`\`\`

## Commit

\`<type>: <description>\` unless this repo's commitlint/hooks say otherwise — check before the first commit.

## Common Commands

\`\`\`bash
${PKG_SCRIPTS:-# Fill in run commands}
${MONO_NOTE}
\`\`\`

## Key Rules

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
