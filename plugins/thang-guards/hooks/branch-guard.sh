#!/usr/bin/env bash
# branch-guard.sh — Warn/block direct push to main or master
# Trigger: PreToolUse(Bash) when command contains "git push"
# Exit 2 to block, 0 to allow

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

CURRENT_BRANCH=$(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Claude Code delivers the tool call as JSON on stdin. There is no CLAUDE_TOOL_INPUT env
# var — reading one left PUSH_COMMAND empty, so no branch was ever guarded.
HOOK_INPUT=$(cat 2>/dev/null || echo "")
PUSH_COMMAND=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$PUSH_COMMAND" ] && PUSH_COMMAND=$(printf '%s' "$HOOK_INPUT" \
  | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

# ─── Detect force push to protected branches ─────────────────────────────────

if echo "$PUSH_COMMAND" | grep -qE 'git push.*(-f|--force|--force-with-lease)'; then
  if echo "$CURRENT_BRANCH $PUSH_COMMAND" | grep -qE '\b(main|master|develop|dev)\b'; then
    echo "" >&2
    echo "🚫 BLOCKED — force push to protected branch: $CURRENT_BRANCH" >&2
    echo "   Explicitly requested force pushes must be done manually." >&2
    echo "" >&2
    exit 2
  fi
fi

# ─── Warn on direct push to main/master ──────────────────────────────────────

if echo "$CURRENT_BRANCH" | grep -qE '^(main|master)$'; then
  echo "" >&2
  echo "⚠️  WARNING: Pushing directly to '$CURRENT_BRANCH'" >&2
  echo "   Consider: create a branch + PR instead." >&2
  echo "   Proceeding in 3 seconds unless you cancel (Ctrl+C)..." >&2
  echo "" >&2
  sleep 3 2>/dev/null || true
fi

# ─── Warn if pushing with uncommitted changes ────────────────────────────────

if ! git -C "$PROJECT_DIR" diff --quiet 2>/dev/null; then
  echo "⚠️  WARNING: You have uncommitted local changes that will NOT be pushed." >&2
fi

exit 0
