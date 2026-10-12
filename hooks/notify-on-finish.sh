#!/usr/bin/env bash
# notify-on-finish.sh — Stop: macOS notification when Claude finishes a turn, so long runs don't need watching.
# No-op off macOS. Never blocks.

command -v osascript >/dev/null 2>&1 || exit 0
PROJECT=$(basename "${CLAUDE_PROJECT_DIR:-$(pwd)}")
osascript -e "display notification \"Finished — waiting for you\" with title \"Claude · ${PROJECT//\"/}\"" >/dev/null 2>&1 || true
exit 0
