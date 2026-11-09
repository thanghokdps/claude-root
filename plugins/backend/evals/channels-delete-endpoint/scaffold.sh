#!/usr/bin/env bash
# Seeds a small NestJS + Drizzle channels app: session guard, zod pipe, global filter, owner-scoped repository,
# one GET route, one drizzle-kit migration, Vitest route tests.
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
git init -q -b main
git config user.email eval@example.com && git config user.name eval
cp -R "$here/repo/." .
git add -A && git commit -qm "init: channels module"
