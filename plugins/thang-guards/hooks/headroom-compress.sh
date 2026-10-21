#!/bin/bash
# headroom-compress.sh — PostToolUse(Bash): soft hint to use headroom_compress on very large output.
# Register WITHOUT asyncRewake: { "matcher": "Bash", "hooks": [{ "type": "command", "command": "~/.claude/hooks/headroom-compress.sh" }] }
# Exit 2 / asyncRewake surfaced every big output as a blocking error and re-woke the model, so this
# emits additionalContext instead (non-blocking), at most once per session, and only when the
# headroom MCP is registered. Read is excluded: a file being edited must stay verbatim.

INPUT=$(cat 2>/dev/null)
[ -z "$INPUT" ] && exit 0
grep -q '"headroom"' "$HOME/.claude.json" 2>/dev/null || exit 0

LEN=$(printf '%s' "$INPUT" | jq -r '.tool_response | tostring' 2>/dev/null | wc -c | tr -d ' ')
[ "${LEN:-0}" -gt "${HEADROOM_WARN_THRESHOLD:-20000}" ] || exit 0

SID=$(printf '%s' "$INPUT" | jq -r '.session_id // "nosession"' 2>/dev/null)
MARK="${TMPDIR:-/tmp}/headroom-hinted-$SID"
[ -f "$MARK" ] && exit 0
touch "$MARK"

jq -cn --arg kb "$((LEN / 1024))" '{hookSpecificOutput: {hookEventName: "PostToolUse",
  additionalContext: ("headroom: that Bash output was ~" + $kb + "KB. If the session will keep running long, consider headroom_compress on bulky logs; skip it when you need the exact text. (Shown once per session.)")}}'
exit 0
