#!/usr/bin/env bash
# Warn when a kit kept on two remotes (GitHub + GitLab) would install a stale copy.
# Usage: remote-drift.sh <kit dir> <marketplace source line, e.g. "Git (<url>)" or "Folder (<dir>)">
# The install source may carry commits of its own (the company copy's merges from main); it is stale only
# when another remote's HEAD is not in its history. Prints nothing when in line; always exits 0.
KIT=$1 SOURCE=$2
git -C "$KIT" rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ "$(git -C "$KIT" remote | wc -l)" -ge 2 ] || exit 0

heads=$(for r in $(git -C "$KIT" remote); do
  printf '%s %s\n' "$r" "$(git -C "$KIT" ls-remote "$r" HEAD 2>/dev/null | cut -f1)"; done)
src=$(for r in $(git -C "$KIT" remote); do
  url=$(git -C "$KIT" remote get-url "$r" 2>/dev/null)
  case "$SOURCE" in (*"($url)"*) echo "$r" ;; esac; done | head -1)
show() { printf '%s\n' "$heads" | awk '{print "    " $1 " " substr($2, 1, 12)}'; }

if [ -n "$src" ]; then
  src_head=$(printf '%s\n' "$heads" | awk -v r="$src" '$1 == r {print $2}')
  [ -n "$src_head" ] || exit 0
  # Only commits already fetched can be compared; an unknown one counts as missing, so the warning errs loud.
  missing=$(printf '%s\n' "$heads" | while read -r r h; do
    [ "$r" = "$src" ] || [ -z "$h" ] || [ "$h" = "$src_head" ] && continue
    git -C "$KIT" merge-base --is-ancestor "$h" "$src_head" 2>/dev/null || printf ' %s' "$r"; done)
  [ -n "$missing" ] || exit 0
  echo "  ⚠️  $src (the install source) lacks commits from:$missing"; show
  echo "     Merge them into the branch $src serves, push it, then re-run this installer."
elif [ "$(printf '%s\n' "$heads" | awk '$2 != "" {print $2}' | sort -u | wc -l)" -gt 1 ]; then
  echo "  ⚠️  the kit's remotes point at different commits:"; show
  echo "     Bring them in line with /sync-remote (ship) before installing on another machine."
fi
exit 0
