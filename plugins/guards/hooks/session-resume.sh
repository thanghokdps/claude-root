#!/usr/bin/env bash
# session-resume.sh — SessionStart: inject specs/HANDOFF.md (written by session-handoff.sh) so a new
# session resumes without being told to, and point at the lesson indexes. Silent when there is nothing. Never blocks.

. "$(dirname "$0")/lib/project-dir.sh"
DIR=$(project_dir "$(jq -r '.cwd // empty' 2>/dev/null)")
HANDOFF="$DIR/specs/HANDOFF.md"
CONTEXT=""

if [ -f "$HANDOFF" ]; then
  CONTEXT="Previous session handoff (specs/HANDOFF.md) — pick up from \"Where it stood\" if the user's request continues it:

$(head -c 8000 "$HANDOFF")"
  rm -f "$HANDOFF"  # injected once; the next Stop rewrites it
fi

# Same folder as learn-promote.py personal_dir(): <repo>-<sha1 of the resolved git common dir, 8 chars>.
PERSONAL=""
COMMON=$(git -C "$DIR" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
if [ -n "$COMMON" ] && REAL=$(cd "$COMMON" 2>/dev/null && pwd -P); then
  PERSONAL="$HOME/.claude/claude-learn/solutions/$(basename "$(dirname "$REAL")")-$(printf '%s' "$REAL" | shasum | cut -c1-8)/INDEX.md"
fi

for idx in "$DIR/.claude/docs/solutions/INDEX.md" "$PERSONAL" "$HOME/.claude/docs/solutions/INDEX.md"; do
  [ -n "$idx" ] && [ -f "$idx" ] && CONTEXT="${CONTEXT:+$CONTEXT

}Learnings index available: $idx — read it before repeating past work."
done

[ -n "$CONTEXT" ] || exit 0
jq -cn --arg c "$CONTEXT" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $c}}'
exit 0
