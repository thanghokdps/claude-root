#!/usr/bin/env bash
# Builds an Expo app repo tagged v1.3.0 with one merged feature since, and a CHANGELOG with no 1.4.0 section.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/base/." .
git add -A && git commit -qm "chore: release 1.3.0"
git tag -a v1.3.0 -m "1.3.0"
cp -R "$here/change/." .
git add -A && git commit -qm "feat: offline mode for the order list"
