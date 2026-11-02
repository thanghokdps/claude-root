#!/usr/bin/env bash
# format-on-edit.sh — PostToolUse(Edit|Write): format the edited file with the project's own formatter.
# Only runs a formatter the project already has (no downloads: npx --no-install). Never blocks.

INPUT=$(cat 2>/dev/null)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -n "$FILE" ] && [ -f "$FILE" ] || exit 0

. "$(dirname "$0")/lib/project-dir.sh"
PROJECT_DIR=$(project_dir "$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)")
cd "$PROJECT_DIR" || exit 0

case "$FILE" in
  *.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs|*.json|*.css|*.scss|*.md|*.astro|*.vue)
    if compgen -G '.prettierrc*' >/dev/null || compgen -G 'prettier.config.*' >/dev/null || grep -q '"prettier"' package.json 2>/dev/null; then
      npx --no-install prettier --write --log-level silent "$FILE" >/dev/null 2>&1 || true
    fi
    ;;
  *.py)
    command -v ruff >/dev/null 2>&1 && ruff format --quiet "$FILE" >/dev/null 2>&1 || true
    ;;
esac

exit 0
