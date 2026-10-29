#!/usr/bin/env bash
# Same repo and docs as docs-sync-route; this branch only renames a local inside a handler.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
shared="$here/../docs-sync-route"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$shared/base/." .
mkdir -p .claude && cp -R "$shared/claude-docs" .claude/docs
git add -A && git commit -qm "init: orders API with docs"
git update-ref refs/remotes/origin/main main
git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/main
git checkout -qb refactor/order-naming
cp -R "$here/change/." .
git add -A && git commit -qm "refactor: clearer local name in getOrder"
