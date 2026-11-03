#!/usr/bin/env bash
# Gives the confined sandbox an offline pnpm: clones the store scripts/eval-plugin.sh --real-scaffold warmed from
# warm/*/package.json into HOME (the sandbox reads and writes only HOME and TMPDIR). The workspace stays empty.
set -euo pipefail
cache="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)/.eval-cache/pnpm"
[ -d "$cache/store" ] || { echo "no warmed store at $cache: run scripts/eval-plugin.sh with --real-scaffold" >&2; exit 1; }
cp -c -R "$cache/store" "$HOME/.pnpm-store"
cp -c -R "$cache/metadata" "$HOME/.pnpm-cache"
cat >"$HOME/.npmrc" <<EOF
store-dir=$HOME/.pnpm-store
cache-dir=$HOME/.pnpm-cache
offline=true
manage-package-manager-versions=false
EOF
# /usr/bin/git is the xcrun shim, which fails in the sandbox (exit 72). The sandbox takes no shell snapshot, so .zshrc
# is never read: every zsh reads .zshenv, and a login zsh reads .zprofile after /etc/zprofile's path_helper, which
# puts /usr/bin back in front. Bash scripts the agent runs (preflight.sh) inherit that PATH.
path_line="export PATH=\"$(dirname "$(xcrun --find git)"):\$PATH\""
echo "$path_line" >"$HOME/.zshenv"
echo "$path_line" >"$HOME/.zprofile"
cat >"$HOME/.gitconfig" <<'EOF'
[user]
	name = Eval Run
	email = eval@example.invalid
[init]
	defaultBranch = main
EOF
