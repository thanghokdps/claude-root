#!/usr/bin/env bash
# Seeds an app where one question is answered by a line in config.py and the other is an auth choice both code paths support.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init"
