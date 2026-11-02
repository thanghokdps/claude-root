#!/bin/bash

# PreToolUse hook (every tool): stop a subagent that is stuck in a loop.
# Counts tool calls per session + subagent and blocks once one passes
# CLAUDE_STEP_LIMIT (default 90). The blocked agent can still answer in text,
# so it ends its turn with a report instead of burning more calls.
# The main session is not counted unless CLAUDE_STEP_LIMIT_MAIN=1.
# A counter older than CLAUDE_STEP_TTL_S (default 6h) starts again at 0.

INPUT=$(cat)

LIMIT="${CLAUDE_STEP_LIMIT:-90}"
TTL="${CLAUDE_STEP_TTL_S:-21600}"

SESSION=$(printf '%s' "$INPUT" | jq -r '.session_id // "nosession"' 2>/dev/null)
AGENT=$(printf '%s' "$INPUT" | jq -r '.agent_id // ""' 2>/dev/null)

if [ -z "$AGENT" ]; then
  [ "${CLAUDE_STEP_LIMIT_MAIN:-0}" = "1" ] || exit 0
  AGENT="main"
fi

case "$LIMIT" in ''|*[!0-9]*) exit 0 ;; esac

DIR="${TMPDIR:-/tmp}/claude-step-limit"
mkdir -p "$DIR" 2>/dev/null || exit 0
FILE="$DIR/$(printf '%s_%s' "$SESSION" "$AGENT" | tr -c 'A-Za-z0-9_.-' '_')"

COUNT=0
if [ -f "$FILE" ]; then
  NOW=$(date +%s)
  MTIME=$(stat -c %Y "$FILE" 2>/dev/null || stat -f %m "$FILE" 2>/dev/null || echo "$NOW")
  if [ $((NOW - MTIME)) -lt "$TTL" ]; then
    COUNT=$(cat "$FILE" 2>/dev/null)
    case "$COUNT" in ''|*[!0-9]*) COUNT=0 ;; esac
  fi
fi
COUNT=$((COUNT + 1))
printf '%s' "$COUNT" > "$FILE" 2>/dev/null

if [ "$COUNT" -gt "$LIMIT" ]; then
  echo "Step limit reached: $((COUNT - 1)) tool calls in this agent (limit $LIMIT). Stop calling tools. Reply with what is done, what is stuck, and the last error, so the main session can re-plan. Raise CLAUDE_STEP_LIMIT only if the task really needs more calls." >&2
  exit 2
fi

exit 0
