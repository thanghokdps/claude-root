#!/usr/bin/env bash
# Seeds a small orders module; the tracker is faked by the issue text pasted in the prompt.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init"
