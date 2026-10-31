#!/usr/bin/env bash
# notify-on-finish.sh — Stop: macOS notification when Claude finishes a turn, so long runs don't need watching.
# No-op off macOS. Never blocks.
# Acts on the event's cwd (process cwd only when .cwd is empty).

command -v osascript >/dev/null 2>&1 || exit 0
CWD=$(jq -r '.cwd // empty' 2>/dev/null)
PROJECT=$(basename "${CWD:-${CLAUDE_PROJECT_DIR:-$(pwd)}}")
osascript -e "display notification \"Finished — waiting for you\" with title \"Claude · ${PROJECT//\"/}\"" >/dev/null 2>&1 || true
exit 0
