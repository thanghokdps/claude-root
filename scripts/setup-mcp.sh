#!/usr/bin/env bash
# setup-mcp.sh — register the MCP servers this kit's workflows assume, at user scope.
# Idempotent: skips servers already registered. Undo: claude mcp remove <name> -s user
set -euo pipefail

command -v claude >/dev/null || { echo "claude CLI not found"; exit 1; }

add() {
  local name="$1"; shift
  if claude mcp get "$name" >/dev/null 2>&1; then
    echo "   $name: already registered"
  else
    claude mcp add -s user "$name" "$@" && echo "   $name: added"
  fi
}

# Drive and verify the running web app from a session (needs Node.js).
add playwright -- npx -y @playwright/mcp@latest

# GitHub tools come from the official `github` plugin (/plugin); GitLab work uses the glab CLI.
echo "Restart Claude Code sessions to pick up new servers."
