#!/bin/bash

# PreToolUse hook (Bash): before a push or a PR/MR, ask the user when no check ran
# after the last change. "Check" = a test, lint, typecheck, build or eval command in
# the run log that run-log.sh writes (<git-dir>/claude-run-log.jsonl); "last change"
# = the newest file time among the files the push carries. Asks, never blocks: the
# user can still push. No run log, nothing to push or no git → stays silent.

INPUT=$(cat)

CMD=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
printf '%s' "$CMD" | grep -qE '(^|[;&|[:space:]])(git[[:space:]]+push|gh[[:space:]]+pr[[:space:]]+create|glab[[:space:]]+mr[[:space:]]+create)([[:space:]]|$)' || exit 0

CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // ""' 2>/dev/null)
[ -n "$CWD" ] && cd "$CWD" 2>/dev/null
TOP=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
LOG="$(git rev-parse --git-dir)/claude-run-log.jsonl"
[ -s "$LOG" ] || exit 0

UPSTREAM=$(git rev-parse --abbrev-ref '@{upstream}' 2>/dev/null || git rev-parse --abbrev-ref origin/HEAD 2>/dev/null)
[ -n "$UPSTREAM" ] || exit 0
FILES=$(git diff --name-only "$UPSTREAM"...HEAD 2>/dev/null)
[ -n "$FILES" ] || exit 0

NEWEST=0
while IFS= read -r f; do
  [ -f "$TOP/$f" ] || continue
  T=$(stat -c %Y "$TOP/$f" 2>/dev/null || stat -f %m "$TOP/$f" 2>/dev/null || echo 0)
  [ "$T" -gt "$NEWEST" ] && NEWEST=$T
done <<< "$FILES"
[ "$NEWEST" -gt 0 ] || exit 0

LAST_CHECK=$(jq -r '
  select(.cmd | test("(^|[ /;&|])(test|tests|pytest|vitest|jest|playwright|lint|eslint|ruff|tsc|typecheck|build|check\\.sh|eval|e2e)([ :;&|.]|$)"))
  | select(.interrupted != true) | .ts' "$LOG" 2>/dev/null | tail -1)
CHECK_EPOCH=0
if [ -n "$LAST_CHECK" ]; then
  CHECK_EPOCH=$(date -u -d "$LAST_CHECK" +%s 2>/dev/null || date -u -j -f '%Y-%m-%dT%H:%M:%SZ' "$LAST_CHECK" +%s 2>/dev/null || echo 0)
fi
[ "$CHECK_EPOCH" -ge "$NEWEST" ] && exit 0

if [ "$CHECK_EPOCH" -eq 0 ]; then
  WHY="no test, lint, build or eval command is in the run log"
else
  WHY="the last check ran at $LAST_CHECK, before the last change to the pushed files"
fi

jq -cn --arg why "$WHY" '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "ask",
    permissionDecisionReason: ("push-evidence: " + $why + ". Run the checks first (then /create-pr can cite them), or allow to push anyway.")
  }
}'
exit 0
