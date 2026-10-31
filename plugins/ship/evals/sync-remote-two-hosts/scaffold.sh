#!/usr/bin/env bash
# A work repo with two bare remotes (origin = github.com, lab = gitlab.com) kept in a temp dir:
#   main        origin is one commit ahead of lab  -> protected
#   feat/only-gh   exists only on origin           -> push
#   feat/lab-ahead lab is one commit ahead of origin -> push
set -euo pipefail
base="$(mktemp -d)"
hub="$base/github.com/app.git"; lab="$base/gitlab.com/app.git"
mkdir -p "$hub" "$lab"
git -C "$hub" init -q --bare -b main
git -C "$lab" init -q --bare -b main
git init -q -b main
git config user.email eval@example.com && git config user.name eval
git remote add origin "$hub" && git remote add lab "$lab"
echo "# app" > README.md
git add -A && git commit -qm "init"
git push -q origin main && git push -q lab main
git checkout -qb feat/lab-ahead
git commit -q --allow-empty -m "lab-ahead 1" && git push -q origin feat/lab-ahead
git commit -q --allow-empty -m "lab-ahead 2" && git push -q lab feat/lab-ahead
git checkout -qb feat/only-gh main
git commit -q --allow-empty -m "only on github" && git push -q origin feat/only-gh
git checkout -q main
git commit -q --allow-empty -m "main moved on github" && git push -q origin main
