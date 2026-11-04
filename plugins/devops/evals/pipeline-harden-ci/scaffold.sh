#!/usr/bin/env bash
# Seeds a GitHub Actions workflow with an unpinned action, no permissions block, an unguarded deploy job and a scripts/check.sh gate.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
chmod +x scripts/check.sh
# The sensitive-path hook answers `ask`, which the don't-ask run denies: without this the write never lands for the grader's file focus.
mkdir -p .claude && printf '!.github/workflows/**\n' >.claude/sensitive-paths.txt
git add -A && git commit -qm "init: ci workflow"
