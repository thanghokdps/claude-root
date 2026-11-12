#!/usr/bin/env bash
# state-dir.sh — sourced by hooks: where this person's Claude state lives, outside every repo.
# Identical copies in core, dev and guards (lint-kit checks it); learn-promote.py computes the same paths.
# Not under ~/.claude: Claude Code refuses Write/Edit there even with permissions.additionalDirectories.

# harness_home: the root, ${XDG_DATA_HOME:-~/.local/share}/claude-harness (global/ and repos/ below it).
harness_home() {
  printf '%s/claude-harness\n' "${XDG_DATA_HOME:-$HOME/.local/share}"
}

# state_dir <dir>: the folder for the repo at <dir> (specs/, solutions/), keyed by its resolved git
# common dir so every worktree shares it: repos/<repo>-<first 8 of sha1(path)>. Fails outside a repo.
state_dir() {
  local common real
  common=$(git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  real=$(cd "$common" 2>/dev/null && pwd -P) || return 1
  printf '%s/repos/%s-%s\n' "$(harness_home)" "$(basename "$(dirname "$real")")" \
    "$(printf '%s' "$real" | shasum | cut -c1-8)"
}

# ticket_dir <dir>: the contract folder (/ticket) of the branch <type>/<id>-<slug> checked out at <dir>:
# specs/<id>-<slug>/ in the state dir, else specs/<id>[-_]*/ or specs/<id>/. Fails off a ticket branch or with no folder.
ticket_dir() {
  local branch state d
  branch=$(git -C "$1" symbolic-ref --short HEAD 2>/dev/null) || return 1
  [[ $branch =~ ^[A-Za-z0-9_.-]+/([A-Za-z]+-[0-9]+|[0-9]+)([-_]|$) ]] || return 1
  state=$(state_dir "$1") || return 1
  for d in "$state/specs/${branch#*/}" "$state/specs/${BASH_REMATCH[1]}"[-_]* "$state/specs/${BASH_REMATCH[1]}"; do
    [ -d "$d" ] && printf '%s\n' "$d" && return 0
  done
  return 1
}

# handoff_file <dir>: per checkout, since parallel worktree sessions share the state dir:
# specs/HANDOFF.md for the main checkout, specs/HANDOFF-<worktree folder>.md for a linked worktree.
handoff_file() {
  local state own common
  state=$(state_dir "$1") || return 1
  own=$(git -C "$1" rev-parse --path-format=absolute --git-dir 2>/dev/null) || return 1
  common=$(git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  if [ "$own" = "$common" ]; then
    printf '%s/specs/HANDOFF.md\n' "$state"
  else
    printf '%s/specs/HANDOFF-%s.md\n' "$state" "$(basename "$(git -C "$1" rev-parse --show-toplevel)")"
  fi
}
