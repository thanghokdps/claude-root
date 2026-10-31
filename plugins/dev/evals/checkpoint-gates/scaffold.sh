#!/usr/bin/env bash
# Seeds PLAN.md with 2 done and 1 open task, commits for the done ones, and one red unittest for the open task.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init"
git commit -q --allow-empty -m "T1: add_note stores a note with tags"
git commit -q --allow-empty -m "T2: list_notes returns notes newest first"
