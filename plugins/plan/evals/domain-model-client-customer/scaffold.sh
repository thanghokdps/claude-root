#!/usr/bin/env bash
# Seeds a repo where one table is called "client" in orders.py and "customer" in invoices.py; no glossary exists yet.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: orders and invoices"
