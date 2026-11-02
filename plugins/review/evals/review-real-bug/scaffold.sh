#!/usr/bin/env bash
# Builds a git repo: base/ on main (also as origin/HEAD), change/ committed on feat/pagination.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/base/." .
git add -A && git commit -qm "init: product list"
git update-ref refs/remotes/origin/main main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
git checkout -qb feat/pagination
cp -R "$here/change/." .
git add -A && git commit -qm "feat: paginate the product list"
