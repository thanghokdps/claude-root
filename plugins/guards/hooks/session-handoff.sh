#!/bin/bash

# Stop hook: write a comprehensive HANDOFF.md at session end.
# Next session reads this automatically via CLAUDE.md — no manual update needed.

INPUT=$(cat 2>/dev/null)
. "$(dirname "$0")/lib/project-dir.sh"
cd "$(project_dir "$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)")" 2>/dev/null || exit 0
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

# Collect open specs: a PLAN.md marked **Status:** complete (plan-format.md) is done.
OPEN_SPECS=$(ls "$REPO_DIR/specs"/*/SUMMARY.md 2>/dev/null | while read f; do
  slug=$(basename "$(dirname "$f")")
  lane=$(grep -iE '^Lane:' "$f" 2>/dev/null | head -1 | sed 's/Lane: *//')
  status=$(grep -m1 -iE '^\*\*Status:\*\*' "$(dirname "$f")/PLAN.md" 2>/dev/null | sed -E 's/^\*\*Status:\*\* *//I')
  [[ "$status" =~ ^[Cc]omplete ]] && continue
  echo "  - $slug ($lane, ${status:-no status})"
done)

# The last reply says where the work stands; the Stop event carries it, older versions only the transcript.
LAST_REPLY=$(printf '%s' "$INPUT" | jq -r '.last_assistant_message // empty' 2>/dev/null)
TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
if [ -z "$LAST_REPLY" ] && [ -f "$TRANSCRIPT" ]; then
  LAST_REPLY=$(jq -rs 'map(select(.type == "assistant") | [.message.content[]? | select(.type == "text") | .text]
    | join("\n") | select(. != "")) | last // empty' "$TRANSCRIPT" 2>/dev/null)
fi
LAST_REPLY=$(printf '%s\n' "$LAST_REPLY" | tail -n 25 | sed 's/^/> /')

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

## Where it stood (end of the last reply)
${LAST_REPLY:-  unknown}

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
