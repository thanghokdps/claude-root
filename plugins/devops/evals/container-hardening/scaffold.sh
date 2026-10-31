#!/usr/bin/env bash
# Seeds a Node service whose Dockerfile uses node:latest, runs as root, copies the whole context and bakes an API key via ENV.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: orders service"
