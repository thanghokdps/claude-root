#!/bin/bash

# PostToolUse hook (Bash): record each command the session ran, so a PR's
# Demonstration can cite what was really run instead of what the model says it ran.
# One JSON line per command in <git-dir>/claude-run-log.jsonl: inside .git, so it
# is never committed. Keeps the command (300 chars) and the last output line
# (160 chars); /create-pr reads it through its witness script.

INPUT=$(cat)

GIT_DIR=$(git rev-parse --git-dir 2>/dev/null) || exit 0
LOG="$GIT_DIR/claude-run-log.jsonl"

printf '%s' "$INPUT" | jq -c '{
  ts: (now | todate),
  session: (.session_id // ""),
  cmd: ((.tool_input.command // "") | .[0:300]),
  last: (((.tool_response.stdout // "") | rtrimstr("\n") | split("\n") | last // "") | .[0:160]),
  interrupted: (.tool_response.interrupted // false)
}' >> "$LOG" 2>/dev/null

exit 0
