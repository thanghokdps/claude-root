#!/usr/bin/env bash
# Seeds a tiny stdlib todo app with unittest tests; the reminder request leaves delivery, window and storage open.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init"
