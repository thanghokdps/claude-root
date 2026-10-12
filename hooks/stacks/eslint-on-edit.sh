#!/usr/bin/env bash
# eslint-on-edit.sh — Run eslint --fix on edited TS/JS files after Edit/Write tool use
# Trigger: PostToolUse(Edit|Write). Hook input arrives as JSON on stdin.

FILE=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)

[ -z "$FILE" ] && exit 0
[[ "$FILE" =~ \.(ts|tsx|js|jsx)$ ]] || exit 0
[ ! -f "$FILE" ] && exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR" || exit 0

# Only the project's own eslint (no download); don't block on unfixable issues.
if compgen -G '.eslintrc*' >/dev/null || compgen -G 'eslint.config.*' >/dev/null; then
  npx --no-install eslint --fix --quiet "$FILE" >/dev/null 2>&1 || true
fi

exit 0
