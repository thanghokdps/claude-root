#!/usr/bin/env bash
# Seeds a repo where two callers reach into three notification senders and the tests patch smtplib.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: notify, signup, billing"
