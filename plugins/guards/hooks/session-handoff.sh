#!/bin/bash

# Stop hook: write a comprehensive HANDOFF.md at session end.
# Next session reads this automatically via CLAUDE.md — no manual update needed.

REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_DIR" ] && exit 0

SPECS_DIR="$REPO_DIR/specs"
HANDOFF="$SPECS_DIR/HANDOFF.md"
mkdir -p "$SPECS_DIR"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "detached")
LAST_COMMITS=$(git log --oneline -8 2>/dev/null | sed 's/^/  /')
STAGED=$(git diff --cached --name-only 2>/dev/null)
UNSTAGED=$(git diff --name-only 2>/dev/null)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | head -10)

# Collect open specs
OPEN_SPECS=$(ls "$REPO_DIR/specs"/*/SUMMARY.md 2>/dev/null | while read f; do
  slug=$(basename "$(dirname "$f")")
  lane=$(grep -iE '^Lane:' "$f" 2>/dev/null | head -1 | sed 's/Lane: *//')
  echo "  - $slug ($lane)"
done)

# Collect unresolved escalations
ESCALATIONS=$(grep -rl "decision: pending" "$REPO_DIR/specs" 2>/dev/null | sed 's|.*/specs/||;s|/.*||' | sort -u | sed 's/^/  - /')

cat > "$HANDOFF" << EOF
# Session Handoff — $TIMESTAMP

> Auto-generated at session end. Read this at the start of the next session.
> Delete after reading and starting new work.

## Branch
\`$BRANCH\`

## Last commits
$LAST_COMMITS

## Git state
EOF

if [ -n "$STAGED" ]; then
  echo "### Staged (ready to commit)" >> "$HANDOFF"
  echo "$STAGED" | sed 's/^/  /' >> "$HANDOFF"
fi

if [ -n "$UNSTAGED" ]; then
  echo "### Unstaged (modified)" >> "$HANDOFF"
  echo "$UNSTAGED" | sed 's/^/  /' >> "$HANDOFF"
fi

if [ -n "$UNTRACKED" ]; then
  echo "### Untracked" >> "$HANDOFF"
  echo "$UNTRACKED" | sed 's/^/  /' >> "$HANDOFF"
fi

cat >> "$HANDOFF" << EOF

## Open specs
${OPEN_SPECS:-  none}

## Unresolved escalations (BLOCK until decided)
${ESCALATIONS:-  none}

## What to do next
<!-- Agent: fill this in by reading the last few messages of the session -->
_See specs/STATE.md for session breadcrumbs_

## Context to reload
- Project docs: \`.claude/docs/index.md\`
- Solutions: \`.claude/docs/solutions/INDEX.md\`
- Global solutions: \`~/.claude/docs/solutions/INDEX.md\`

EOF

# Large session hint
TOTAL_CHANGED=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
TOTAL_STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
TOTAL=$((TOTAL_CHANGED + TOTAL_STAGED))

if [ "$TOTAL" -ge 5 ]; then
  echo "" >> "$HANDOFF"
  echo "> ⚠ $TOTAL files changed this session. Run \`/compound\` to crystallize learnings before closing." >> "$HANDOFF"
fi

echo "[HANDOFF] Written to specs/HANDOFF.md" >&2
exit 0
