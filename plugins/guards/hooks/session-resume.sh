#!/usr/bin/env bash
# session-resume.sh — SessionStart: inject <state dir>/specs/HANDOFF.md (written by session-handoff.sh) so a new
# session resumes without being told to, and point at the lesson indexes. Silent when there is nothing. Never blocks.

. "$(dirname "$0")/lib/project-dir.sh"
. "$(dirname "$0")/lib/state-dir.sh"
DIR=$(project_dir "$(jq -r '.cwd // empty' 2>/dev/null)")
STATE=$(state_dir "$DIR")
HANDOFF=$(handoff_file "$DIR")
CONTEXT=""

if [ -n "$HANDOFF" ] && [ -f "$HANDOFF" ]; then
  CONTEXT="Previous session handoff ($HANDOFF) — pick up from \"Where it stood\" if the user's request continues it:

$(head -c 8000 "$HANDOFF")"
  rm -f "$HANDOFF"  # injected once; the next Stop rewrites it
fi

for idx in "$DIR/.claude/solutions/INDEX.md" "${STATE:+$STATE/solutions/INDEX.md}" \
  "$(harness_home)/global/solutions/INDEX.md"; do
  [ -n "$idx" ] && [ -f "$idx" ] && CONTEXT="${CONTEXT:+$CONTEXT

}Learnings index available: $idx — read it before repeating past work."
done

[ -n "$CONTEXT" ] || exit 0
jq -cn --arg c "$CONTEXT" '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $c}}'
exit 0
