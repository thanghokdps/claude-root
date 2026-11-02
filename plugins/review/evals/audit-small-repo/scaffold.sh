#!/usr/bin/env bash
# Seeds a small bank CLI with a planted injection, an overdraft and a dead function, as one commit.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: branch office account tool"
