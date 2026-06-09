#!/usr/bin/env bash
# setup-headroom.sh — Install and wire headroom context compression
#
# What it does:
#   1. Create venv at ~/.headroom-env with Python 3.12
#   2. pip install headroom-ai[all,mcp] into venv
#   3. headroom wrap claude  (starts proxy on port 8787)
#   4. claude mcp add headroom --scope user
#
# Usage: bash scripts/setup-headroom.sh
# Requires: Python 3.12 (brew install python@3.12), claude CLI

set -euo pipefail

VENV="$HOME/.headroom-env"
HEADROOM="$VENV/bin/headroom"

echo "📦 Creating venv and installing headroom-ai..."
python3.12 -m venv "$VENV"
"$VENV/bin/pip" install "headroom-ai[all,mcp]" --quiet

echo "⚙️  Registering headroom MCP server (user scope)..."
claude mcp add headroom --scope user -- "$HEADROOM" mcp serve 2>/dev/null || \
  echo "   (MCP server already registered — skipping)"

echo ""
echo "✅  Headroom wired."
echo ""
echo "   venv             — $VENV"
echo "   MCP tools        — headroom_compress · headroom_retrieve · headroom_stats"
echo "   headroom learn   — run manually after failed sessions"
echo ""
echo "To verify: claude mcp list"
