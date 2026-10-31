#!/usr/bin/env bash
# Seeds a minimal Expo Router app (theme tokens, Button primitive, typed param list); nothing installed.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: expo app skeleton"
