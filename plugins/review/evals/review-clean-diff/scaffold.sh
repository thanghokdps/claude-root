#!/usr/bin/env bash
# Builds a git repo: base/ on main (also as origin/HEAD), change/ committed on feat/item-count.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/base/." .
git add -A && git commit -qm "init: cart totals"
git update-ref refs/remotes/origin/main main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
git checkout -qb feat/item-count
cp -R "$here/change/." .
git add -A && git commit -qm "feat: count items in the cart"
