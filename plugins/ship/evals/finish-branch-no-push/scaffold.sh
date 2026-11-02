#!/usr/bin/env bash
# Builds a repo with main and feat/slugify (2 commits); origin/HEAD points at main, but there is no real remote.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/base/." .
git add -A && git commit -qm "init: text utils"
git update-ref refs/remotes/origin/main main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
git checkout -qb feat/slugify
cp -R "$here/change1/." .
git add -A && git commit -qm "feat: add slugify"
cp -R "$here/change2/." .
git add -A && git commit -qm "test: cover slugify"
