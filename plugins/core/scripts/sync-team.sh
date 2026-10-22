#!/usr/bin/env bash
# sync-team.sh — Pull latest code, rebuild memory from your last commit forward
# Usage: ./sync-team.sh [project-dir]
#
# For multi-person teams:
#   1. Fetch + pull latest from remote
#   2. Find your last commit (by git author)
#   3. Collect your commits from last known → HEAD
#   4. Summarize what changed in each of YOUR commits
#   5. Write to .claude/memory/commits/ and update MEMORY.md
#   6. Flag any conflicts or areas to re-check

set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"
CLAUDE_DIR="$PROJECT_DIR/.claude"
MEMORY_DIR="$CLAUDE_DIR/memory"
GIT_USER="$(git -C "$PROJECT_DIR" config user.name 2>/dev/null || echo "")"
GIT_EMAIL="$(git -C "$PROJECT_DIR" config user.email 2>/dev/null || echo "")"
TODAY="$(date +%Y-%m-%d)"
NOW="$(date +%Y-%m-%dT%H:%M:%S)"

if [ -z "$GIT_USER" ]; then
  echo "❌ No git user.name configured. Run: git config user.name 'Your Name'"
  exit 1
fi

echo "🔄 Syncing team repo for: $GIT_USER"
echo "   Project: $PROJECT_DIR"
echo ""

# ─── 1. Stash any uncommitted changes ────────────────────────────────────────

STASHED=false
if ! git -C "$PROJECT_DIR" diff --quiet 2>/dev/null || ! git -C "$PROJECT_DIR" diff --cached --quiet 2>/dev/null; then
  echo "📦 Stashing uncommitted changes..."
  git -C "$PROJECT_DIR" stash push -m "harness-sync-$(date +%s)" --include-untracked
  STASHED=true
fi

# ─── 2. Find your last known commit (from memory) ────────────────────────────

LAST_KNOWN_HASH=""
if [ -f "$MEMORY_DIR/commits/last-sync.txt" ]; then
  LAST_KNOWN_HASH=$(cat "$MEMORY_DIR/commits/last-sync.txt" | head -1)
fi

# Verify hash still exists (it may have been rebased/force-pushed)
if [ -n "$LAST_KNOWN_HASH" ]; then
  if ! git -C "$PROJECT_DIR" cat-file -e "$LAST_KNOWN_HASH" 2>/dev/null; then
    echo "⚠️  Last known hash $LAST_KNOWN_HASH no longer exists — starting from 14 days ago"
    LAST_KNOWN_HASH=""
  fi
fi

# ─── 3. Pull latest ──────────────────────────────────────────────────────────

echo "⬇️  Pulling latest..."
REMOTE_BRANCH="$(git -C "$PROJECT_DIR" rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "")"
if [ -n "$REMOTE_BRANCH" ]; then
  git -C "$PROJECT_DIR" fetch --all --prune
  git -C "$PROJECT_DIR" pull --rebase=false 2>/dev/null || {
    echo "⚠️  Pull had conflicts — resolve manually before proceeding"
    $STASHED && git -C "$PROJECT_DIR" stash pop 2>/dev/null || true
    exit 1
  }
else
  echo "   (no remote tracking branch — skipping pull)"
fi

# ─── 4. Collect YOUR commits since last sync ─────────────────────────────────

if [ -n "$LAST_KNOWN_HASH" ]; then
  SINCE_ARG="$LAST_KNOWN_HASH..HEAD"
  echo "📋 Scanning your commits since $LAST_KNOWN_HASH..."
else
  SINCE_ARG="--since=14.days"
  echo "📋 Scanning your commits from last 14 days..."
fi

# Get your commits (most recent first)
MY_COMMITS=$(git -C "$PROJECT_DIR" log $SINCE_ARG \
  --author="$GIT_USER" \
  --format="%H|%ai|%s" \
  --no-merges 2>/dev/null || \
  git -C "$PROJECT_DIR" log $SINCE_ARG \
  --author="$GIT_EMAIL" \
  --format="%H|%ai|%s" \
  --no-merges 2>/dev/null || echo "")

if [ -z "$MY_COMMITS" ]; then
  echo "   No new commits from you since last sync."
else
  COMMIT_COUNT=$(echo "$MY_COMMITS" | grep -c '^' || true)
  echo "   Found $COMMIT_COUNT commit(s) from you"
fi

# ─── 5. Build memory entries ─────────────────────────────────────────────────

mkdir -p "$MEMORY_DIR/commits"
OUTFILE="$MEMORY_DIR/commits/$TODAY.md"

{
  echo "---"
  echo "name: commits-$TODAY"
  echo "description: Commits by $GIT_USER on $TODAY (team sync)"
  echo "metadata:"
  echo "  type: project"
  echo "---"
  echo ""
  echo "# Commits — $TODAY (synced $NOW)"
  echo ""
} > "$OUTFILE"

if [ -n "$MY_COMMITS" ]; then
  echo "$MY_COMMITS" | while IFS='|' read -r hash date subject; do
    echo "## \`${hash:0:8}\` — $date"
    echo ""
    echo "**$subject**"
    echo ""

    # Files changed
    FILES=$(git -C "$PROJECT_DIR" diff-tree --no-commit-id -r --name-only "$hash" 2>/dev/null | head -20)
    if [ -n "$FILES" ]; then
      echo "Files changed:"
      echo "\`\`\`"
      echo "$FILES"
      echo "\`\`\`"
    fi
    echo ""
  done >> "$OUTFILE"

  # Save last sync hash
  echo "$MY_COMMITS" | head -1 | cut -d'|' -f1 > "$MEMORY_DIR/commits/last-sync.txt"
fi

# ─── 6. Scan what teammates changed (highlight conflicts) ────────────────────

TEAM_CHANGES=$(git -C "$PROJECT_DIR" log $SINCE_ARG \
  --not --author="$GIT_USER" \
  --format="%H|%an|%s" \
  --no-merges 2>/dev/null | head -20 || echo "")

if [ -n "$TEAM_CHANGES" ]; then
  echo "" >> "$OUTFILE"
  echo "---" >> "$OUTFILE"
  echo "" >> "$OUTFILE"
  echo "# Team changes since last sync (top 20)" >> "$OUTFILE"
  echo "" >> "$OUTFILE"

  echo "$TEAM_CHANGES" | while IFS='|' read -r hash author subject; do
    echo "- \`${hash:0:8}\` **[$author]** $subject" >> "$OUTFILE"
  done
fi

# ─── 7. Update MEMORY.md index ───────────────────────────────────────────────

if [ -f "$MEMORY_DIR/MEMORY.md" ]; then
  ENTRY="- [Commits $TODAY](commits/$TODAY.md) — $COMMIT_COUNT commit(s) by $GIT_USER; team sync"

  # Remove old entry for today if exists, then append
  grep -v "Commits $TODAY" "$MEMORY_DIR/MEMORY.md" > "$MEMORY_DIR/MEMORY.md.tmp" 2>/dev/null && \
    mv "$MEMORY_DIR/MEMORY.md.tmp" "$MEMORY_DIR/MEMORY.md"
  echo "$ENTRY" >> "$MEMORY_DIR/MEMORY.md"
fi

# ─── 8. Pop stash ────────────────────────────────────────────────────────────

if $STASHED; then
  echo ""
  echo "📦 Restoring stashed changes..."
  git -C "$PROJECT_DIR" stash pop 2>/dev/null || {
    echo "⚠️  Stash pop had conflicts — check git stash list"
  }
fi

# ─── Summary ─────────────────────────────────────────────────────────────────

echo ""
echo "✅  Sync complete"
echo "   Memory saved to: .claude/memory/commits/$TODAY.md"
if [ -n "$TEAM_CHANGES" ]; then
  TEAM_COUNT=$(echo "$TEAM_CHANGES" | grep -c '^' || echo "0")
  echo "   ⚠️  $TEAM_COUNT team commits — review .claude/memory/commits/$TODAY.md for context"
fi
echo ""
