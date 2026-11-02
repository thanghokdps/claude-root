#!/usr/bin/env bash
# ruff-on-edit.sh — Auto-fix Python files with ruff after Edit/Write tool use
# Trigger: PostToolUse(Edit|Write). Hook input arrives as JSON on stdin.

FILE=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)

[ -z "$FILE" ] && exit 0
[[ "$FILE" != *.py ]] && exit 0
[ ! -f "$FILE" ] && exit 0
command -v ruff >/dev/null 2>&1 || exit 0

# Run ruff fix (auto-fixable issues) + format
ruff check --fix --quiet "$FILE" >/dev/null 2>&1 || true
ruff format --quiet "$FILE" >/dev/null 2>&1 || true

exit 0
