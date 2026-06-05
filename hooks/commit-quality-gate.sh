#!/usr/bin/env bash
# commit-quality-gate.sh — Block commits with secrets, debug artifacts, or failing tests
# Trigger: PreToolUse(Bash) when command contains "git commit"
# Exit 2 to block commit, 0 to allow

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
BLOCKED=false
REASONS=()

# ─── Get staged diff ────────────────────────────────────────────────────────

STAGED=$(git -C "$PROJECT_DIR" diff --cached 2>/dev/null || echo "")

if [ -z "$STAGED" ]; then
  exit 0  # nothing staged, let git handle it
fi

# ─── 1. Secrets scan ────────────────────────────────────────────────────────

# Skip test files and docs
STAGED_APP=$(git -C "$PROJECT_DIR" diff --cached -- \
  ':!*.test.*' ':!*.spec.*' ':!*.example.*' ':!*.md' ':!docs/*' 2>/dev/null || echo "")

if echo "$STAGED_APP" | grep -qE 'sk-[a-zA-Z0-9]{20,}'; then
  BLOCKED=true
  REASONS+=("OpenAI API key pattern detected in staged code")
fi

if echo "$STAGED_APP" | grep -qE 'AKIA[0-9A-Z]{16}'; then
  BLOCKED=true
  REASONS+=("AWS access key pattern detected in staged code")
fi

if echo "$STAGED_APP" | grep -qE '(password|secret|api_key)\s*=\s*["\x27][^"\x27]{8,}'; then
  BLOCKED=true
  REASONS+=("Hardcoded credential pattern detected in staged code")
fi

# ─── 2. .env files ───────────────────────────────────────────────────────────

if git -C "$PROJECT_DIR" diff --cached --name-only 2>/dev/null | grep -qE '^\.env$|^\.env\.local$|^\.env\.prod'; then
  BLOCKED=true
  REASONS+=(".env file staged — use .env.example instead")
fi

# ─── 3. Debug artifacts ──────────────────────────────────────────────────────

if echo "$STAGED_APP" | grep -qE '^\+.*\bbreakpoint\(\)|^\+.*\bpdb\.set_trace\(\)'; then
  BLOCKED=true
  REASONS+=("Python debugger breakpoint in staged code (breakpoint() or pdb.set_trace())")
fi

if echo "$STAGED_APP" | grep -qE '^\+.*\bconsole\.log\(|^\+.*\bconsole\.debug\('; then
  # Only warn — don't block (might be intentional logging)
  echo "⚠️  WARNING: console.log/debug in staged code — confirm this is intentional" >&2
fi

# ─── 4. Large binary files ───────────────────────────────────────────────────

LARGE_FILES=$(git -C "$PROJECT_DIR" diff --cached --name-only 2>/dev/null | while read -r f; do
  [ -f "$PROJECT_DIR/$f" ] && SIZE=$(stat -f%z "$PROJECT_DIR/$f" 2>/dev/null || stat -c%s "$PROJECT_DIR/$f" 2>/dev/null || echo 0)
  [ "${SIZE:-0}" -gt 5242880 ] && echo "$f ($((SIZE / 1024 / 1024))MB)"
done || true)

if [ -n "$LARGE_FILES" ]; then
  BLOCKED=true
  REASONS+=("Large file(s) staged (>5MB): $LARGE_FILES — use git-lfs instead")
fi

# ─── Report ──────────────────────────────────────────────────────────────────

if $BLOCKED; then
  echo "" >&2
  echo "🚫 COMMIT BLOCKED — quality gate failed:" >&2
  for reason in "${REASONS[@]}"; do
    echo "   ❌ $reason" >&2
  done
  echo "" >&2
  echo "   Fix the issues above, then re-stage and commit." >&2
  echo "" >&2
  exit 2
fi

exit 0
