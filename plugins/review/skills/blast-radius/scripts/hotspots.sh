#!/bin/bash

# Prints the files changed most often in git history: the code many features
# pass through, where a change needs the closest review.
# Usage: hotspots.sh [since] [count]   (default: "12 months ago", 15)
# Lockfiles, generated and vendored files are left out; deleted files too.

SINCE="${1:-12 months ago}"
COUNT="${2:-15}"
git rev-parse --git-dir >/dev/null 2>&1 || { echo "hotspots: not a git repo."; exit 0; }

git log --since="$SINCE" --no-merges --name-only --format= 2>/dev/null \
  | grep -v '^$' \
  | grep -vE '(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb|poetry\.lock|uv\.lock|Cargo\.lock|go\.sum)$' \
  | grep -vE '(^|/)(node_modules|dist|build|vendor|\.next|coverage)/|\.min\.(js|css)$|\.snap$' \
  | sort | uniq -c | sort -rn \
  | while read -r n f; do [ -e "$f" ] && printf '%5d  %s\n' "$n" "$f"; done \
  | head -n "$COUNT"
exit 0
