#!/usr/bin/env bash
# eslint-on-edit.sh — Run eslint --fix on edited TS/JS files after Edit tool use
# Trigger: PostToolUse(Edit) on .ts / .tsx / .js / .jsx files

FILE="${CLAUDE_TOOL_RESULT_FILE:-}"
if [ -z "$FILE" ]; then
  FILE=$(echo "${CLAUDE_TOOL_INPUT:-}" | grep -oE '"file_path"\s*:\s*"([^"]+\.(ts|tsx|js|jsx))"' | head -1 | cut -d'"' -f4)
fi

[ -z "$FILE" ] && exit 0
[[ "$FILE" =~ \.(ts|tsx|js|jsx)$ ]] || exit 0
[ ! -f "$FILE" ] && exit 0

# Run eslint --fix silently (don't block on unfixable issues)
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

if [ -f "$PROJECT_DIR/.eslintrc*" ] || [ -f "$PROJECT_DIR/eslint.config*" ]; then
  npx eslint --fix --quiet "$FILE" 2>/dev/null || true
fi

exit 0
