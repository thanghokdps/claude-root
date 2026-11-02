#!/usr/bin/env bash
# Seeds a small Terraform module (S3 bucket) with prod and staging tfvars; no backend, nothing to install.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: exports bucket module"
