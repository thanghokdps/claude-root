#!/usr/bin/env bash
# ruff-on-edit.sh — Auto-fix Python files with ruff after Edit tool use
# Trigger: PostToolUse(Edit) on .py files

FILE="${CLAUDE_TOOL_RESULT_FILE:-}"
if [ -z "$FILE" ]; then
  # Try to extract from tool input
  FILE=$(echo "${CLAUDE_TOOL_INPUT:-}" | grep -oE '"file_path"\s*:\s*"([^"]+\.py)"' | head -1 | cut -d'"' -f4)
fi

[ -z "$FILE" ] && exit 0
[[ "$FILE" != *.py ]] && exit 0
[ ! -f "$FILE" ] && exit 0

# Run ruff fix (auto-fixable issues) + format
ruff check --fix --silent "$FILE" 2>/dev/null || true
ruff format --silent "$FILE" 2>/dev/null || true

exit 0
