#!/usr/bin/env bash
# session-resume.sh — SessionStart: inject specs/HANDOFF.md (written by session-handoff.sh) so a new
# session resumes without being told to. Silent when there is nothing to resume. Never blocks.

DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
HANDOFF="$DIR/specs/HANDOFF.md"
[ -f "$HANDOFF" ] || exit 0

CONTEXT="Previous session handoff (specs/HANDOFF.md) — continue from its Next steps, then delete the file:

$(head -c 8000 "$HANDOFF")"
for idx in "$DIR/.claude/docs/solutions/INDEX.md" "$HOME/.claude/docs/solutions/INDEX.md"; do
  [ -f "$idx" ] && CONTEXT="$CONTEXT

Learnings index available: $idx — read it before repeating past work."
done

jq -cn --arg c "$CONTEXT" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $c}}'
exit 0
