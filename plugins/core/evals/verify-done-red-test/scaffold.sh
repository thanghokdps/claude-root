#!/usr/bin/env bash
# Seeds a repo whose unittest suite has one red test (discount above 100% is not capped).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: discount helper"
