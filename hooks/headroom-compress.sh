#!/bin/bash

# PostToolUse(Bash|Read) asyncRewake hook — auto-trigger headroom_compress.
#
# When tool output exceeds HEADROOM_WARN_THRESHOLD (default 8000 chars):
#   - exit 2  → Claude Code injects a system-reminder and re-wakes the model
#   - Claude sees the reminder and automatically calls the headroom_compress MCP tool
#
# When output is small: exit 0 silently (no overhead).

INPUT=$(cat /dev/stdin 2>/dev/null)
[ -z "$INPUT" ] && exit 0

RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // ""' 2>/dev/null)
LEN=${#RESPONSE}
THRESHOLD=${HEADROOM_WARN_THRESHOLD:-8000}

if [ "$LEN" -gt "$THRESHOLD" ]; then
  TOOL=$(echo "$INPUT" | jq -r '.tool_name // "tool"' 2>/dev/null)
  KB=$(( LEN / 1024 ))
  echo "headroom: ${TOOL} output is ~${KB}KB. Call the headroom_compress MCP tool now to compress this content and reduce context before proceeding."
  exit 2
fi

exit 0
