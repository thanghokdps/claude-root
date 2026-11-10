#!/usr/bin/env bash
# sync-team.sh — Pull latest code and report what came in, from git log alone
# Usage: ./sync-team.sh [project-dir]
#
# For multi-person teams:
#   1. Stash uncommitted changes, fetch + pull
#   2. List the commits the pull brought in (HEAD before the pull..HEAD), or the last 14 days when none
#   3. Split them into yours and your teammates'
#   4. Flag files a teammate touched that you also changed in the last 14 days
# Writes nothing: git already holds the history, so no state file can drift from it.

set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"
GIT_USER="$(git -C "$PROJECT_DIR" config user.name 2>/dev/null || echo "")"

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

# ─── 2. Pull latest ──────────────────────────────────────────────────────────

BEFORE="$(git -C "$PROJECT_DIR" rev-parse HEAD)"
echo "⬇️  Pulling latest..."
if git -C "$PROJECT_DIR" rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  git -C "$PROJECT_DIR" fetch --all --prune
  git -C "$PROJECT_DIR" pull --rebase=false 2>/dev/null || {
    echo "⚠️  Pull had conflicts — resolve manually before proceeding"
    $STASHED && git -C "$PROJECT_DIR" stash pop 2>/dev/null || true
    exit 1
  }
else
  echo "   (no remote tracking branch — skipping pull)"
fi

if [ "$(git -C "$PROJECT_DIR" rev-parse HEAD)" != "$BEFORE" ]; then
  RANGE=("$BEFORE..HEAD")
  echo "📋 Commits the pull brought in:"
else
  RANGE=(--since=14.days)
  echo "📋 Nothing new pulled — commits from the last 14 days:"
fi

# ─── 3. Yours and your teammates' ────────────────────────────────────────────

ALL=$(git -C "$PROJECT_DIR" log "${RANGE[@]}" --format="%h|%an|%s" --no-merges 2>/dev/null || true)
# git --author cannot be negated portably, so filter on the author name instead.
MINE=$(echo "$ALL" | awk -F'|' -v u="$GIT_USER" 'NF && $2 == u')
TEAM=$(echo "$ALL" | awk -F'|' -v u="$GIT_USER" 'NF && $2 != u' | head -20)

echo ""
echo "Yours ($(echo "$MINE" | grep -c . || true)):"
echo "$MINE" | awk -F'|' 'NF { print "  - `" $1 "` " $3 }'
echo "Team ($(echo "$TEAM" | grep -c . || true), top 20):"
echo "$TEAM" | awk -F'|' 'NF { print "  - `" $1 "` [" $2 "] " $3 }'

# ─── 4. Overlap: files a teammate touched that you changed recently ──────────

MY_FILES=$(git -C "$PROJECT_DIR" log --since=14.days --author="$GIT_USER" --name-only --format= 2>/dev/null | sort -u)
OVERLAP=""
if [ -n "$TEAM" ] && [ -n "$MY_FILES" ]; then
  TEAM_FILES=$(echo "$TEAM" | cut -d'|' -f1 | while read -r h; do
    [ -n "$h" ] && git -C "$PROJECT_DIR" diff-tree --no-commit-id -r --name-only "$h"
  done | sort -u)
  OVERLAP=$(comm -12 <(echo "$MY_FILES") <(echo "$TEAM_FILES") || true)
fi
if [ -n "$OVERLAP" ]; then
  echo ""
  echo "⚠️  Re-check (you and a teammate both changed):"
  echo "$OVERLAP" | sed 's/^/  - /'
fi

# ─── 5. Pop stash ────────────────────────────────────────────────────────────

if $STASHED; then
  echo ""
  echo "📦 Restoring stashed changes..."
  git -C "$PROJECT_DIR" stash pop 2>/dev/null || {
    echo "⚠️  Stash pop had conflicts — check git stash list"
  }
fi

echo ""
echo "✅  Sync complete"
