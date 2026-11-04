#!/usr/bin/env bash
# missing-tools.sh — say when python3 or jq is absent. Trigger: SessionStart.
# The guards fail open without them (branch-guard allows a commit on main, secret-guard allows reading .env,
# repo-profile copies no rules), and nothing else reports it. Plain bash: it must run when both are missing.
missing=""
for tool in python3 jq; do
  command -v "$tool" >/dev/null 2>&1 || missing="$missing $tool"
done
[ -n "$missing" ] || exit 0
note="HARNESS GUARDS OFF: not installed:$missing. Branch, secret and edit guards do nothing, and repo-profile copies no rules, until you install them and start a new session."
printf '{"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s Tell the user this in your first reply."}}\n' "$note" "$note"
exit 0
