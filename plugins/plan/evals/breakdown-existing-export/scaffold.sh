#!/usr/bin/env bash
# Seeds a small orders app where the CSV export by date range already exists and the other two requested items do not.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: orders app"
