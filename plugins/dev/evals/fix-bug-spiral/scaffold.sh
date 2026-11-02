#!/usr/bin/env bash
# Seeds a repo where the test imports src/utils/parse.py while the user kept editing src/parse.py.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: date parsing"
