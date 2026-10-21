#!/usr/bin/env bash
# eval-plugin.sh — run a plugin's evals/ suite with real model calls (paid; not part of check.sh).
#   bash scripts/eval-plugin.sh thang-agent                 # one cheap pass: 1 run per case, no baseline arm
#   bash scripts/eval-plugin.sh thang-agent --runs 3 --ablation with-without   # full comparison before a demo
# The report stays local (--no-publish); later flags override the defaults. Judge is sonnet: the default small judge
# split votes on correct Vietnamese replies (greenfield-problem-first, 2026-10-21).
set -euo pipefail
cd "$(dirname "$0")/.."

plugin="${1:?usage: eval-plugin.sh <plugin> [claude plugin eval options]}"
shift
[ -d "plugins/$plugin/evals" ] || { echo "plugins/$plugin has no evals/ suite" >&2; exit 1; }

claude plugin eval "plugins/$plugin" --trust-plugin --no-publish \
  --runs 1 --ablation none --concurrency 4 --max-cost-usd 3 --judge-model sonnet \
  --allow-tools "Bash(bash *preflight.sh*)" "$@"
