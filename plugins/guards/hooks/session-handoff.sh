#!/bin/bash

# Stop hook (fires after every reply): rewrite HANDOFF.md with only what git and the transcript cannot tell a
# fresh session — open specs, pending escalations, where the last reply left off. session-resume.sh injects it.

INPUT=$(cat 2>/dev/null)
. "$(dirname "$0")/lib/project-dir.sh"
cd "$(project_dir "$(printf '%s' "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)")" 2>/dev/null || exit 0
REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_DIR" ] && exit 0

. "$(dirname "$0")/lib/state-dir.sh"
SPECS_DIR="$(state_dir "$REPO_DIR")/specs" || exit 0
HANDOFF="$(handoff_file "$REPO_DIR")" || exit 0
mkdir -p "$SPECS_DIR" || exit 0

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
BRANCH=$(git symbolic-ref --short HEAD 2>/dev/null || echo "detached")

# Collect open specs: a PLAN.md marked **Status:** complete (plan-format.md) is done.
OPEN_SPECS=$(ls "$SPECS_DIR"/*/SUMMARY.md 2>/dev/null | while read f; do
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
ESCALATIONS=$(grep -rl "decision: pending" "$SPECS_DIR" 2>/dev/null | sed "s|^$SPECS_DIR/||;s|/.*||" | sort -u | sed 's/^/  - /')

cat > "$HANDOFF" << EOF
# Session Handoff — $TIMESTAMP

> Rewritten after every reply; the next fresh session gets it once, then it is deleted.

## Branch
\`$BRANCH\`

## Open specs
${OPEN_SPECS:-  none}

## Unresolved escalations (BLOCK until decided)
${ESCALATIONS:-  none}

## Where it stood (end of the last reply)
${LAST_REPLY:-  unknown}
EOF

# Large session hint
TOTAL_CHANGED=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ')
TOTAL_STAGED=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
TOTAL=$((TOTAL_CHANGED + TOTAL_STAGED))

if [ "$TOTAL" -ge 5 ]; then
  echo "" >> "$HANDOFF"
  echo "> ⚠ $TOTAL files changed this session. Run \`/compound\` to crystallize learnings before closing." >> "$HANDOFF"
fi

echo "[HANDOFF] Written to $HANDOFF" >&2
exit 0
