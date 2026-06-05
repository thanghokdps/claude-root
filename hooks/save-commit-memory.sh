#!/usr/bin/env bash
# save-commit-memory.sh — Auto-save commit info to memory after git commit
# Trigger: PostToolUse(Bash) when command contained "git commit"
# NEVER blocks — all errors exit 0 silently

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
CLAUDE_DIR="$PROJECT_DIR/.claude"
MEMORY_DIR="$CLAUDE_DIR/memory"

[ -d "$MEMORY_DIR" ] || exit 0

TODAY="$(date +%Y-%m-%d 2>/dev/null || echo "unknown")"
NOW="$(date +%Y-%m-%dT%H:%M:%S 2>/dev/null || echo "unknown")"

# ─── Get commit info ─────────────────────────────────────────────────────────

HASH="$(git -C "$PROJECT_DIR" rev-parse --short HEAD 2>/dev/null || echo "")"
LONG_HASH="$(git -C "$PROJECT_DIR" rev-parse HEAD 2>/dev/null || echo "")"
SUBJECT="$(git -C "$PROJECT_DIR" log -1 --format="%s" 2>/dev/null || echo "")"
AUTHOR="$(git -C "$PROJECT_DIR" log -1 --format="%an" 2>/dev/null || echo "")"
BRANCH="$(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
FILES="$(git -C "$PROJECT_DIR" diff-tree --no-commit-id -r --name-only HEAD 2>/dev/null | head -20 || echo "")"

[ -z "$HASH" ] && exit 0  # Not a git repo or commit failed

# ─── Idempotency: don't double-write the same commit ─────────────────────────

mkdir -p "$MEMORY_DIR/commits" 2>/dev/null || exit 0
OUTFILE="$MEMORY_DIR/commits/$TODAY.md"

if [ -f "$OUTFILE" ] && grep -q "$LONG_HASH" "$OUTFILE" 2>/dev/null; then
  exit 0
fi

# ─── Initialize file if new day ──────────────────────────────────────────────

if [ ! -f "$OUTFILE" ]; then
  cat > "$OUTFILE" << EOF || exit 0
---
name: commits-$TODAY
description: Commits on $TODAY
metadata:
  type: project
---

# Commits — $TODAY
EOF
fi

# ─── Append commit entry ─────────────────────────────────────────────────────

{
  echo ""
  echo "## \`$HASH\` — $NOW"
  echo ""
  echo "**$SUBJECT**"
  echo ""
  echo "- Author: $AUTHOR"
  echo "- Branch: \`$BRANCH\`"
  [ -n "$FILES" ] && {
    echo "- Files:"
    echo "\`\`\`"
    echo "$FILES"
    echo "\`\`\`"
  }
  echo ""
} >> "$OUTFILE" 2>/dev/null || exit 0

# ─── Save last-sync pointer ──────────────────────────────────────────────────

[ -n "$LONG_HASH" ] && echo "$LONG_HASH" > "$MEMORY_DIR/commits/last-sync.txt" 2>/dev/null || true

# ─── Update MEMORY.md index ──────────────────────────────────────────────────

if [ -f "$MEMORY_DIR/MEMORY.md" ]; then
  ENTRY="- [Commits $TODAY](commits/$TODAY.md) — commit log for $TODAY"
  grep -q "Commits $TODAY" "$MEMORY_DIR/MEMORY.md" 2>/dev/null || \
    echo "$ENTRY" >> "$MEMORY_DIR/MEMORY.md" 2>/dev/null || true
fi

exit 0
