#!/usr/bin/env bash
# project-dir.sh — sourced by guards hooks: project_dir <event cwd> prints the folder a hook acts on.
# The event's cwd counts only when it is the project or one of its git worktrees (same common git dir):
# in a worktree session CLAUDE_PROJECT_DIR is the main checkout. Any other folder the shell cd'd into
# (a cloned repo) falls back to the project, so its formatter, git config or handoff is never trusted.
project_dir() {
  local cwd=$1 root="${CLAUDE_PROJECT_DIR:-$(pwd)}" mine theirs
  if [ -n "$cwd" ] && [ "$cwd" != "$root" ]; then
    mine=$(git -C "$root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
    theirs=$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)
    if [ -n "$mine" ] && [ "$mine" = "$theirs" ]; then
      git -C "$cwd" rev-parse --show-toplevel 2>/dev/null && return
    fi
  fi
  printf '%s\n' "$root"
}

# outside_project <event cwd>: true when the cwd is in a git repo that is neither the project nor one of its worktrees.
outside_project() {
  local cwd=$1 root="${CLAUDE_PROJECT_DIR:-$(pwd)}" theirs
  [ -n "$cwd" ] || return 1
  theirs=$(git -C "$cwd" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  [ "$theirs" != "$(git -C "$root" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" ]
}
