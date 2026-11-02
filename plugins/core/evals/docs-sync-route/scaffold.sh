#!/usr/bin/env bash
# Builds a git repo with .claude/docs on main (also as origin/HEAD) and a refund route on feat/refund.
# The docs fixture is stored as claude-docs/ so the kit's own path guards don't treat it as live config.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/base/." .
mkdir -p .claude && cp -R "$here/claude-docs" .claude/docs
git add -A && git commit -qm "init: orders API with docs"
git update-ref refs/remotes/origin/main main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
git checkout -qb feat/refund
cp -R "$here/change/." .
git add -A && git commit -qm "feat: refund an order"
