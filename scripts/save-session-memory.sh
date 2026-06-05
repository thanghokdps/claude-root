#!/usr/bin/env bash
# save-session-memory.sh — Save session context to memory after work is done
# Called by state-breadcrumb.sh hook OR manually: ./save-session-memory.sh "summary text"
# Usage: ./save-session-memory.sh [optional-summary]

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CLAUDE_DIR="$PROJECT_DIR/.claude"
MEMORY_DIR="$CLAUDE_DIR/memory"
TODAY="$(date +%Y-%m-%d)"
NOW="$(date +%Y-%m-%dT%H:%M:%S)"
SESSION_ID="${CLAUDE_SESSION_ID:-manual-$(date +%s)}"
SUMMARY="${1:-}"

mkdir -p "$MEMORY_DIR/sessions"

OUTFILE="$MEMORY_DIR/sessions/$TODAY.md"

# Initialize file if new day
if [ ! -f "$OUTFILE" ]; then
  cat > "$OUTFILE" << EOF
---
name: sessions-$TODAY
description: Work sessions on $TODAY
metadata:
  type: project
---

# Sessions — $TODAY
EOF
fi

# ─── Last commit context ──────────────────────────────────────────────────────

LAST_COMMIT=""
LAST_COMMIT_MSG=""
LAST_COMMIT_HASH=""
if git -C "$PROJECT_DIR" rev-parse HEAD &>/dev/null; then
  LAST_COMMIT_HASH=$(git -C "$PROJECT_DIR" rev-parse --short HEAD 2>/dev/null || echo "")
  LAST_COMMIT_MSG=$(git -C "$PROJECT_DIR" log -1 --format="%s" 2>/dev/null || echo "")
  LAST_COMMIT="$LAST_COMMIT_HASH: $LAST_COMMIT_MSG"
fi

# ─── Branch context ───────────────────────────────────────────────────────────

BRANCH=$(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# ─── Append session entry ─────────────────────────────────────────────────────

{
  echo ""
  echo "## Session $SESSION_ID — $NOW"
  echo ""
  echo "**Branch:** \`$BRANCH\`"
  [ -n "$LAST_COMMIT" ] && echo "**Last commit:** \`$LAST_COMMIT\`"
  echo ""
  if [ -n "$SUMMARY" ]; then
    echo "**Summary:** $SUMMARY"
  fi
  echo ""
} >> "$OUTFILE"

# ─── Update MEMORY.md index ───────────────────────────────────────────────────

if [ -f "$MEMORY_DIR/MEMORY.md" ]; then
  ENTRY="- [Sessions $TODAY](sessions/$TODAY.md) — work log for $TODAY"
  if ! grep -q "Sessions $TODAY" "$MEMORY_DIR/MEMORY.md" 2>/dev/null; then
    echo "$ENTRY" >> "$MEMORY_DIR/MEMORY.md"
  fi
fi

exit 0
