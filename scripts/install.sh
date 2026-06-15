#!/usr/bin/env bash
# install.sh — Install Claude harness to a persistent location
# Usage: bash scripts/install.sh [install-dir]
# Default install-dir: ~/.claude-harness
#
# What it does:
#   1. Copy the harness to INSTALL_DIR (default ~/.claude-harness)
#   2. Write HARNESS_DIR export to your shell rc file
#   3. Install skills, rules, hooks into ~/.claude/ (global Claude Code config)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_DIR="${1:-$HOME/.claude-harness}"

echo "🔧 Claude Harness Installer"
echo "   Source : $SOURCE_DIR"
echo "   Target : $INSTALL_DIR"
echo ""

# ─── Copy harness to install dir ──────────────────────────────────────────────

if [ -d "$INSTALL_DIR" ]; then
  echo "⚠️  $INSTALL_DIR already exists."
  printf "   Overwrite? [y/N] "
  read -r CONFIRM
  [[ "$CONFIRM" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 1; }
  rm -rf "$INSTALL_DIR"
fi

cp -r "$SOURCE_DIR" "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/scripts/"*.sh 2>/dev/null || true
chmod +x "$INSTALL_DIR/hooks/"*.sh   2>/dev/null || true
chmod +x "$INSTALL_DIR/hooks/stacks/"*.sh 2>/dev/null || true

echo "✅ Harness copied to $INSTALL_DIR"

# ─── Export HARNESS_DIR in shell config ───────────────────────────────────────

HARNESS_EXPORT="export HARNESS_DIR=\"$INSTALL_DIR\""

add_to_shell_config() {
  local RC_FILE="$1"
  [ -f "$RC_FILE" ] || return 0

  if grep -q "HARNESS_DIR" "$RC_FILE" 2>/dev/null; then
    # macOS sed needs -i ''
    sed -i.bak "s|export HARNESS_DIR=.*|$HARNESS_EXPORT|" "$RC_FILE" 2>/dev/null || \
      sed -i    "s|export HARNESS_DIR=.*|$HARNESS_EXPORT|" "$RC_FILE"
    rm -f "${RC_FILE}.bak"
    echo "   Updated HARNESS_DIR in $(basename "$RC_FILE")"
  else
    { echo ""; echo "# Claude Harness"; echo "$HARNESS_EXPORT"; } >> "$RC_FILE"
    echo "   Added HARNESS_DIR to $(basename "$RC_FILE")"
  fi
}

SHELL_NAME="$(basename "${SHELL:-bash}")"
case "$SHELL_NAME" in
  zsh)  add_to_shell_config "$HOME/.zshrc" ;;
  bash) add_to_shell_config "$HOME/.bashrc"; add_to_shell_config "$HOME/.bash_profile" ;;
  *)    add_to_shell_config "$HOME/.zshrc"; add_to_shell_config "$HOME/.bashrc" ;;
esac

# ─── Install into ~/.claude/ (global Claude Code config) ──────────────────────

echo ""
echo "📦 Installing to ~/.claude/ ..."

CLAUDE_GLOBAL="$HOME/.claude"
mkdir -p "$CLAUDE_GLOBAL"/{skills,rules,hooks,docs/solutions,memory/templates}

if [ -d "$INSTALL_DIR/skills" ]; then
  cp -r "$INSTALL_DIR/skills/"* "$CLAUDE_GLOBAL/skills/" 2>/dev/null || true
  COUNT=$(ls "$CLAUDE_GLOBAL/skills/" 2>/dev/null | wc -l | tr -d ' ')
  echo "   Skills  : $COUNT installed"
fi

if [ -d "$INSTALL_DIR/rules" ]; then
  cp "$INSTALL_DIR/rules/"*.md "$CLAUDE_GLOBAL/rules/" 2>/dev/null || true
  COUNT=$(ls "$CLAUDE_GLOBAL/rules/"*.md 2>/dev/null | wc -l | tr -d ' ')
  echo "   Rules   : $COUNT installed"
fi

if [ -d "$INSTALL_DIR/hooks" ]; then
  cp "$INSTALL_DIR/hooks/"*.sh "$CLAUDE_GLOBAL/hooks/" 2>/dev/null || true
  chmod +x "$CLAUDE_GLOBAL/hooks/"*.sh 2>/dev/null || true
  COUNT=$(ls "$CLAUDE_GLOBAL/hooks/"*.sh 2>/dev/null | wc -l | tr -d ' ')
  echo "   Hooks   : $COUNT installed"
fi

if [ -d "$INSTALL_DIR/memory" ]; then
  cp -r "$INSTALL_DIR/memory/"* "$CLAUDE_GLOBAL/memory/templates/" 2>/dev/null || true
  echo "   Memory  : templates copied"
fi

# ─── Write HARNESS_DIR into ~/.claude settings so skills can read it ──────────

SETTINGS="$CLAUDE_GLOBAL/settings.json"
if [ -f "$SETTINGS" ]; then
  # Inject HARNESS_DIR into env block if it exists, otherwise skip (user manages manually)
  echo "   settings.json: found (not modified — register hooks manually if needed)"
else
  echo "   settings.json: not found (run /init-project in a project to generate one)"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────

echo ""
echo "✅ Installation complete!"
echo ""
echo "   HARNESS_DIR = $INSTALL_DIR"
echo ""
echo "Next steps:"
echo "  1. Reload your shell:    source ~/.zshrc   (or open a new terminal)"
echo "  2. Bootstrap a project:  cd my-project && \$HARNESS_DIR/scripts/init.sh"
echo "  3. Or open Claude Code and type: /init-project"
echo ""
echo "To update the harness later:"
echo "  bash \$HARNESS_DIR/scripts/install.sh"
echo ""
