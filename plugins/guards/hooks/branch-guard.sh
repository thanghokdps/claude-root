#!/usr/bin/env bash
# branch-guard.sh — Block any direct push to environment branches (dev, stag, prod) and
# force/delete pushes to protected ones; warn on a direct push to main or master
# Trigger: PreToolUse(Bash) when command contains "git push"
# Exit 2 to block, 0 to allow

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"

CURRENT_BRANCH=$(git -C "$PROJECT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Claude Code delivers the tool call as JSON on stdin. There is no CLAUDE_TOOL_INPUT env
# var — reading one left PUSH_COMMAND empty, so no branch was ever guarded.
HOOK_INPUT=$(cat 2>/dev/null || echo "")
PUSH_COMMAND=$(printf '%s' "$HOOK_INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$PUSH_COMMAND" ] && PUSH_COMMAND=$(printf '%s' "$HOOK_INPUT" \
  | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

# ─── Block force, delete or mirror pushes that reach a protected branch ─────
# A safety net against accidental history rewrites, not a security boundary: server-side
# branch protection is the real control. Every `git … push` segment is read word by word, so
# flags elsewhere on the line (`gh pr create --base main --body-file …`, a `-f` inside
# `feat/dev-fullstack`) never count. Whatever the guard cannot parse fails closed.

PROTECTED_RE='^(main|master|develop|dev|stag|stage|staging|prod|production)$'

# Environment branches deploy on push, so code reaches them only through a PR. Override with
# HARNESS_ENV_BRANCHES="dev qa prod" (space-separated names; anything but [A-Za-z0-9._/-] is dropped;
# set but empty turns the check off).
ENV_BRANCHES=${HARNESS_ENV_BRANCHES-dev develop stag stage staging prod production}
ENV_RE=""
for name in $ENV_BRANCHES; do
  [[ "$name" =~ ^[A-Za-z0-9._/-]+$ ]] && ENV_RE+="${ENV_RE:+|}${name//./\\.}"
done
[ -n "$ENV_RE" ] && ENV_RE="^(${ENV_RE})$"
FORCE_RE='^(-[a-zA-Z]*f[a-zA-Z]*|--for.*)$'                     # -f, -uf, --force[-with-lease[=…]|-if-includes]
DELETE_RE='^(-[a-zA-Z]*d[a-zA-Z]*|--de(l(e(t(e)?)?)?)?)$'
ALL_REFS_RE='^--(al|all|br|bra|bran|branc|branch|branche|branches)$'
MIRROR_RE='^--mi(r(r(o(r)?)?)?)?$'                             # git accepts unique long-option prefixes
VALUE_OPT_RE='^(-o|--push-option|--receive-pack|--exec|--repo)$'   # the next word is their value
GIT_VALUE_OPT_RE='^(-C|-c|--git-dir|--work-tree|--namespace|--exec-path|--config-env)$'
EXPANSION_RE='[][$`{}*?~]'
RISKY_RE='(^|[[:space:]"'"'"'])(-[a-zA-Z]*[fd][a-zA-Z]*|--for|--de|--mi|--al|--br|\+)'
SHELL_STRING_RE='(^|[^[:alnum:]_])(eval|xargs|(ba|z|da|k)?sh[[:space:]]+-[a-z]*c)([^[:alnum:]_]|$)'

block() {
  echo "" >&2
  echo "🚫 BLOCKED — $1 (branch: $CURRENT_BRANCH)" >&2
  echo "   Push a feature branch and open a PR; force, delete and mirror pushes must be done manually." >&2
  echo "" >&2
  exit 2
}

target_ref() {
  local ref=${1#+}
  ref=${ref##*:}; printf '%s' "${ref#refs/heads/}"
}

is_protected_ref() { [[ "$(target_ref "$1")" =~ $PROTECTED_RE ]]; }
is_env_ref() { [ -n "$ENV_RE" ] && [[ "$(target_ref "$1")" =~ $ENV_RE ]]; }

# Strips subshell parens and quotes. `$`, backticks and braces stay (a `{ … }` group is its own
# word), so a substituted or brace-expanded target still reads as unresolved.
clean_word() {
  local w=$1
  while [[ "$w" == [\(\"\']* ]]; do w=${w:1}; done
  while [[ "$w" == *[\)\"\'] ]]; do w=${w%?}; done
  printf '%s' "${w//\\/}"
}

# Prints the reason to block one push (its arguments after `push`), or nothing.
check_push() {
  local -a args=("$@")
  local i tok force=0 delete=0 all_refs=0 unresolved=0 protected=0 env="" remote="" refspecs=0 upstream spec configured
  for ((i = 0; i < ${#args[@]}; i++)); do
    tok=${args[$i]}
    [[ "$tok" =~ $MIRROR_RE ]] && { echo "mirror push overwrites every branch"; return; }
    [[ "$tok" =~ $VALUE_OPT_RE ]] && { i=$((i + 1)); continue; }
    [[ "$tok" =~ $FORCE_RE ]] && { force=1; continue; }
    [[ "$tok" =~ $DELETE_RE ]] && { delete=1; continue; }
    [[ "$tok" =~ $ALL_REFS_RE ]] && { all_refs=1; continue; }
    [[ "$tok" == -* ]] && continue
    [[ "$tok" =~ $EXPANSION_RE ]] && { unresolved=1; continue; }
    if [ -z "$remote" ]; then remote=$tok; continue; fi
    refspecs=$((refspecs + 1))
    [[ "$tok" == +* ]] && force=1
    [[ "$tok" == :* ]] && delete=1
    is_protected_ref "$tok" && protected=1
    is_env_ref "$tok" && env=$(target_ref "$tok")
  done

  if [ "$refspecs" -eq 0 ]; then                                # no refspec: config decides what is pushed
    [ -z "$remote" ] && remote=$(git -C "$PROJECT_DIR" config --get "branch.$CURRENT_BRANCH.remote" 2>/dev/null || echo origin)
    configured=$(git -C "$PROJECT_DIR" config --get-all "remote.$remote.push" 2>/dev/null || true)
    if [ -n "$configured" ]; then
      while IFS= read -r spec; do
        [[ "$spec" == +* ]] && force=1
        is_protected_ref "$spec" && protected=1
        is_env_ref "$spec" && env=$(target_ref "$spec")
      done <<<"$configured"
    else
      is_protected_ref "$CURRENT_BRANCH" && protected=1
      is_env_ref "$CURRENT_BRANCH" && env=$CURRENT_BRANCH
      upstream=$(git -C "$PROJECT_DIR" config --get "branch.$CURRENT_BRANCH.merge" 2>/dev/null || true)
      [ -n "$upstream" ] && is_protected_ref "$upstream" && protected=1
      [ -n "$upstream" ] && is_env_ref "$upstream" && env=$(target_ref "$upstream")
      [ "$(git -C "$PROJECT_DIR" config --get push.default 2>/dev/null)" = "matching" ] && all_refs=1
    fi
  fi

  if [ "$force" -eq 1 ] || [ "$delete" -eq 1 ]; then
    [ "$all_refs" -eq 1 ] && { echo "forced or deleting push of all branches"; return; }
    [ "$unresolved" -eq 1 ] && { echo "forced or deleting push to a target the guard cannot resolve"; return; }
    [ "$protected" -eq 1 ] && { echo "forced or deleting push to a protected branch"; return; }
  fi
  [ -n "$env" ] && echo "direct push to environment branch '$env' — merge it through a PR"
}

# Prints the reason to block one shell segment, or nothing.
check_segment() {
  local -a raw words=() alias_words
  local w i j=-1 cmd="" alias_value
  read -ra raw <<<"$1"
  [ "${#raw[@]}" -eq 0 ] && return
  for w in "${raw[@]}"; do words+=("$(clean_word "$w")"); done

  for i in "${!words[@]}"; do
    w=${words[$i]//[\`\$\(]/}
    [[ "${w##*/}" == "git" ]] && { j=$i; break; }
  done
  [ "$j" -lt 0 ] && return

  for ((i = j + 1; i < ${#words[@]}; i++)); do               # git's own options, then the subcommand
    w=${words[$i]}
    if [[ "$w" =~ $GIT_VALUE_OPT_RE ]]; then
      i=$((i + 1))
      [[ "$w" == "-c" && "${words[$i]:-}" =~ ^(remote\..*\.push|push\.default)= ]] \
        && { echo "push config set on the command line"; return; }
      continue
    fi
    [[ "$w" == -* ]] && continue
    cmd=$w; break
  done
  [ -z "$cmd" ] && return

  if [ "$cmd" = "push" ]; then
    check_push "${words[@]:$((i + 1))}"
    return
  fi
  alias_value=$(git -C "$PROJECT_DIR" config --get "alias.$cmd" 2>/dev/null || true)
  [ -z "$alias_value" ] && return
  if [[ "$alias_value" == '!'* ]]; then
    [[ "$alias_value" == *push* && "$alias_value" =~ $RISKY_RE ]] && echo "shell alias '$cmd' runs a push the guard cannot check"
    return
  fi
  read -ra alias_words <<<"$alias_value"
  [ "${alias_words[0]:-}" = "push" ] && check_push "${alias_words[@]:1}" "${words[@]:$((i + 1))}"
}

PUSH_COMMAND=${PUSH_COMMAND//$'\\\n'/ }                         # join backslash-newline continuations

if [[ "$PUSH_COMMAND" == *push* && "$PUSH_COMMAND" =~ $SHELL_STRING_RE && "$PUSH_COMMAND" =~ $RISKY_RE ]]; then
  block "push inside eval, xargs or a shell string the guard cannot parse"
fi

while IFS= read -r segment; do
  reason=$(check_segment "$segment")
  [ -n "$reason" ] && block "$reason"
done < <(printf '%s\n' "$PUSH_COMMAND" | tr ';&|' '\n\n\n')

# ─── Warn on direct push to main/master ──────────────────────────────────────

if echo "$CURRENT_BRANCH" | grep -qE '^(main|master)$'; then
  echo "" >&2
  echo "⚠️  WARNING: Pushing directly to '$CURRENT_BRANCH'" >&2
  echo "   Consider: create a branch + PR instead." >&2
  echo "   Proceeding in 3 seconds unless you cancel (Ctrl+C)..." >&2
  echo "" >&2
  sleep 3 2>/dev/null || true
fi

# ─── Warn if pushing with uncommitted changes ────────────────────────────────

if ! git -C "$PROJECT_DIR" diff --quiet 2>/dev/null; then
  echo "⚠️  WARNING: You have uncommitted local changes that will NOT be pushed." >&2
fi

exit 0
