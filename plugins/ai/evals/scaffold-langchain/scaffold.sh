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
# Identity for the scaffold's commits; git itself must already be ahead of /usr/bin on PATH (scripts/eval-plugin.sh).
cat >"$HOME/.gitconfig" <<'EOF'
[user]
	name = Eval Run
	email = eval@example.invalid
[init]
	defaultBranch = main
EOF
