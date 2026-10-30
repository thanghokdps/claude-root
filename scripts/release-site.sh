#!/usr/bin/env bash
# release-site.sh — deploy the docs site to Vercel production. Git pushes no longer deploy
# (vercel.json: git.deploymentEnabled false); this is the only way a release ships.
#
#   VERCEL_DEPLOY_HOOK_URL=<hook> bash scripts/release-site.sh
#
# The hook URL comes from Vercel → Project → Settings → Git → Deploy Hooks (branch main).
# Anyone holding it can trigger a deploy: keep it in your shell env or a secret store, never commit it.
set -euo pipefail

if [ -z "${VERCEL_DEPLOY_HOOK_URL:-}" ]; then
  echo "VERCEL_DEPLOY_HOOK_URL is not set — create a Deploy Hook in Vercel → Project → Settings → Git" >&2
  exit 2
fi

curl -fsS -X POST "$VERCEL_DEPLOY_HOOK_URL"
echo
echo "Deploy queued — follow it on the Vercel dashboard."
