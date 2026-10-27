#!/usr/bin/env bash
# sync-remote.sh — compare a repo's GitHub and GitLab remotes and print the pushes that would sync them.
#   bash sync-remote.sh [repo-dir] [remote-a remote-b]
# Read-only apart from `git fetch`: it never pushes. Each push it plans is printed as its own command,
# so the agent runs them one by one and the branch-guard hook checks every one.
# Output, one row per ref, tab-separated: <kind> <ref> <detail> <command>
#   same · push (fast-forward or create; safe to run) · protected (main/env branch; the user runs it) ·
#   diverged · tag-conflict (never pushed) · tag-push
# Exit: 0 ok · 3 not exactly two remotes found (rows list the remotes) · 4 not a git repo
set -uo pipefail

dir=${1:-.}
git -C "$dir" rev-parse --git-dir >/dev/null 2>&1 || { printf 'error\t%s\tnot a git repository\t\n' "$dir"; exit 4; }
g() { git -C "$dir" "$@"; }

if [ $# -ge 3 ]; then
  A=$2; B=$3
else
  A=""; B=""
  while read -r name url; do
    case "$url" in
      *github*) [ -z "$A" ] && A=$name ;;
      *gitlab*) [ -z "$B" ] && B=$name ;;
    esac
  done < <(g remote -v | awk '$3=="(fetch)"{print $1, $2}')
  if [ -z "$A" ] || [ -z "$B" ]; then
    g remote -v | awk '$3=="(fetch)"{printf "remote\t%s\t%s\t\n", $1, $2}'
    exit 3
  fi
fi

ENV_BRANCHES=${HARNESS_ENV_BRANCHES-dev develop stag stage staging prod production}
is_protected() {
  local b=$1 p
  for p in main master $ENV_BRANCHES; do [ "$b" = "$p" ] && return 0; done
  return 1
}

for r in "$A" "$B"; do
  g fetch -q --prune --no-tags "$r" "+refs/heads/*:refs/sync-remote/$r/heads/*" "+refs/tags/*:refs/sync-remote/$r/tags/*" 2>/dev/null \
    || { printf 'error\t%s\tfetch failed (auth or network)\t\n' "$r"; exit 4; }
done

sha() { g rev-parse -q --verify "$1^{commit}" 2>/dev/null || true; }
row() { printf '%s\t%s\t%s\t%s\n' "$@"; }

plan_branch() {
  local b=$1 sa sb
  sa=$(sha "refs/sync-remote/$A/heads/$b"); sb=$(sha "refs/sync-remote/$B/heads/$b")
  local from to src detail
  if [ "$sa" = "$sb" ]; then row same "$b" "${sa:0:8}" ""; return; fi
  if [ -z "$sb" ]; then from=$A; to=$B; src=$sa; detail="only on $A"
  elif [ -z "$sa" ]; then from=$B; to=$A; src=$sb; detail="only on $B"
  elif g merge-base --is-ancestor "$sb" "$sa"; then from=$A; to=$B; src=$sa; detail="$A ahead of $B by $(g rev-list --count "$sb..$sa")"
  elif g merge-base --is-ancestor "$sa" "$sb"; then from=$B; to=$A; src=$sb; detail="$B ahead of $A by $(g rev-list --count "$sa..$sb")"
  else
    row diverged "$b" "$A ${sa:0:8} and $B ${sb:0:8} each have commits the other lacks" ""; return
  fi
  local cmd="git -C $dir push $to refs/sync-remote/$from/heads/$b:refs/heads/$b"
  if is_protected "$b"; then row protected "$b" "$detail" "$cmd"; else row push "$b" "$detail" "$cmd"; fi
}

plan_tag() {
  local t=$1 ta tb
  ta=$(g rev-parse -q --verify "refs/sync-remote/$A/tags/$t" 2>/dev/null || true)
  tb=$(g rev-parse -q --verify "refs/sync-remote/$B/tags/$t" 2>/dev/null || true)
  if [ "$ta" = "$tb" ]; then return
  elif [ -z "$tb" ]; then row tag-push "$t" "only on $A" "git -C $dir push $B refs/sync-remote/$A/tags/$t:refs/tags/$t"
  elif [ -z "$ta" ]; then row tag-push "$t" "only on $B" "git -C $dir push $A refs/sync-remote/$B/tags/$t:refs/tags/$t"
  else row tag-conflict "$t" "$A ${ta:0:8} vs $B ${tb:0:8}" ""
  fi
}

row remotes "$A $B" "$(g remote get-url "$A") ↔ $(g remote get-url "$B")" ""
{ g for-each-ref --format='%(refname)' "refs/sync-remote/$A/heads" "refs/sync-remote/$B/heads" \
    | sed -E 's#^refs/sync-remote/[^/]+/heads/##'; } | sort -u | while read -r b; do plan_branch "$b"; done
{ g for-each-ref --format='%(refname)' "refs/sync-remote/$A/tags" "refs/sync-remote/$B/tags" \
    | sed -E 's#^refs/sync-remote/[^/]+/tags/##'; } | sort -u | while read -r t; do plan_tag "$t"; done
exit 0
