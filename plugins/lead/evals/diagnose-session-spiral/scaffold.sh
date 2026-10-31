#!/usr/bin/env bash
# Seeds a repo holding a hand-written 19-line session transcript (transcript.jsonl).
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: session transcript"
