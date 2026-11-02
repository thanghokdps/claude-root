#!/bin/bash

# Prints the checks this branch really ran, from the run log the guards plugin's
# run-log hook writes (<git-dir>/claude-run-log.jsonl), for a PR's Demonstration.
# Keeps only test, lint, typecheck, build, eval and e2e commands run since the
# branch's first commit. No log → says so; never invents a line.

GIT_DIR=$(git rev-parse --git-dir 2>/dev/null) || { echo "Witness: not a git repo."; exit 0; }
LOG="$GIT_DIR/claude-run-log.jsonl"
[ -s "$LOG" ] || { echo "Witness: not recorded (no run log; the guards plugin's run-log hook writes it)."; exit 0; }

BASE=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null || echo main)
FIRST=$(git log --reverse --format=%cI "$BASE"..HEAD 2>/dev/null | head -1)
SINCE=$(date -u -d "${FIRST:-1970-01-01T00:00:00Z}" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "${FIRST:-1970-01-01T00:00:00Z}")

OUT=$(jq -r --arg since "$SINCE" '
  select(.ts >= $since)
  | select(.cmd | test("(^|[ /;&|])(test|tests|pytest|vitest|jest|playwright|lint|eslint|ruff|tsc|typecheck|build|check\\.sh|eval|e2e)([ :;&|.]|$)"))
  | "- `\(.cmd | gsub("\n"; " ") | .[0:120])` at \(.ts)\(if .interrupted then " (interrupted)" else "" end): \(.last)"
' "$LOG" 2>/dev/null | tail -15)

if [ -z "$OUT" ]; then
  echo "Witness: no test, lint, build or eval command in the run log since $SINCE."
else
  echo "Witness (from the run log, since $SINCE):"
  printf '%s\n' "$OUT"
fi
exit 0
