#!/usr/bin/env bash
# state-breadcrumb.sh — Append session end breadcrumb to memory
# Trigger: SessionEnd hook
# NEVER blocks — all errors exit 0 silently

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CLAUDE_DIR="$PROJECT_DIR/.claude"
MEMORY_DIR="$CLAUDE_DIR/memory"

# Early exit if no memory dir (project not initialized)
[ -d "$MEMORY_DIR" ] || exit 0

TODAY="$(date +%Y-%m-%d 2>/dev/null || echo "unknown")"
NOW="$(date +%Y-%m-%dT%H:%M:%S 2>/dev/null || echo "unknown")"

# ─── Parse session metadata from stdin (JSON if available) ───────────────────

SESSION_ID=""
TURN_COUNT=""

if command -v jq &>/dev/null; then
  INPUT="$(cat /dev/stdin 2>/dev/null || echo '{}')"
  SESSION_ID="$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null || echo "")"
  TURN_COUNT="$(echo "$INPUT" | jq -r '.num_turns // empty' 2>/dev/null || echo "")"
fi

SESSION_ID="${SESSION_ID:-${CLAUDE_SESSION_ID:-session-$(date +%s 2>/dev/null || echo "0")}}"

# ─── Last commit ─────────────────────────────────────────────────────────────

LAST_COMMIT=""
if git -C "$PROJECT_DIR" rev-parse HEAD &>/dev/null 2>&1; then
  LAST_HASH="$(git -C "$PROJECT_DIR" rev-parse --short HEAD 2>/dev/null || echo "")"
  LAST_MSG="$(git -C "$PROJECT_DIR" log -1 --format="%s" 2>/dev/null || echo "")"
  [ -n "$LAST_HASH" ] && LAST_COMMIT="$LAST_HASH: $LAST_MSG"
fi

BRANCH="$(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"

# ─── Idempotency check ───────────────────────────────────────────────────────

mkdir -p "$MEMORY_DIR/sessions" 2>/dev/null || exit 0
OUTFILE="$MEMORY_DIR/sessions/$TODAY.md"

# Don't write duplicate session entries
if [ -f "$OUTFILE" ] && grep -q "$SESSION_ID" "$OUTFILE" 2>/dev/null; then
  exit 0
fi

# ─── Initialize file if new day ──────────────────────────────────────────────

if [ ! -f "$OUTFILE" ]; then
  cat > "$OUTFILE" << EOF || exit 0
---
name: sessions-$TODAY
description: Work sessions on $TODAY
metadata:
  type: project
---

# Sessions — $TODAY

## Session End Log
EOF
fi

# ─── Append entry ────────────────────────────────────────────────────────────

{
  echo ""
  echo "### $NOW — $SESSION_ID"
  echo ""
  [ -n "$LAST_COMMIT" ] && echo "- Last commit: \`$LAST_COMMIT\`"
  [ -n "$BRANCH" ] && echo "- Branch: \`$BRANCH\`"
  [ -n "$TURN_COUNT" ] && echo "- Turns: $TURN_COUNT"
  echo ""
} >> "$OUTFILE" 2>/dev/null || true

# ─── Update MEMORY.md index ──────────────────────────────────────────────────

if [ -f "$MEMORY_DIR/MEMORY.md" ]; then
  ENTRY="- [Sessions $TODAY](sessions/$TODAY.md) — work log for $TODAY"
  grep -q "Sessions $TODAY" "$MEMORY_DIR/MEMORY.md" 2>/dev/null || \
    echo "$ENTRY" >> "$MEMORY_DIR/MEMORY.md" 2>/dev/null || true
fi

exit 0
