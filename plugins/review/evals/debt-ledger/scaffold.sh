#!/usr/bin/env bash
# Seeds a repo with three shortcut: comments (one without an upgrade trigger) and a README decoy, as one commit.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: notifier service"
