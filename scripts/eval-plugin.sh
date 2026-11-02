#!/usr/bin/env bash
# eval-plugin.sh — run a plugin's evals/ suite with real model calls (paid; not part of check.sh).
#   bash scripts/eval-plugin.sh ai                    # one cheap pass: 1 run per case, no baseline arm
#   bash scripts/eval-plugin.sh ai --runs 3 --ablation with-without      # full comparison before a demo
#   bash scripts/eval-plugin.sh ai --real-scaffold    # scaffold-* cases only, with pnpm/npx/git/gh in the sandbox (first argument)
# The report stays local (--no-publish); later flags override the defaults. Judge is sonnet: the default small judge
# split votes on correct Vietnamese replies (greenfield-problem-first, 2026-10-21).
# Target is plugins/, not plugins/<plugin>: a case may only load plugins under the target, and a plugin whose
# dependency is not loaded is dropped from the run, so eval-build.py adds each case's `plugins:` from plugin.json.
# --scaffold runs the cases' own scaffold_script (fixtures authored in this repo).
# The sandbox has no working git and runs in don't-ask mode, so only python is allowed in Bash: a case
# that needs git at run time, or a typed slash command (never a Skill call there), cannot be evaluated.
set -euo pipefail
cd "$(dirname "$0")/.."

plugin="${1:?usage: eval-plugin.sh <plugin> [claude plugin eval options]}"
shift
[ -d "plugins/$plugin/evals" ] || { echo "plugins/$plugin has no evals/ suite" >&2; exit 1; }
build="$(python3 scripts/eval-build.py "$plugin")"

# --real-scaffold: run only the scaffold-* cases (a real project: pnpm, npx, git, gh api; 900 s per case in prompt.md),
# paid ~$1-3 per case. Without it those cases are dropped, so the cheap pass never grants the shell.
tools=("Bash(bash *preflight.sh*)" "Bash(python3 *)" "Bash(python *)" Write Edit)
only=(--concurrency 4 --max-cost-usd 6)
if [ "${1:-}" = "--real-scaffold" ]; then
  shift
  tools+=("Bash(pnpm *)" "Bash(npm *)" "Bash(npx *)" "Bash(node *)" "Bash(git *)" "Bash(gh api *)" "Bash(mkdir *)" "Bash(ls *)" "Bash(cat *)" "Bash(grep *)")
  only=(--case 'scaffold-*' --concurrency 1 --max-cost-usd 6)
else
  rm -rf "$build"/scaffold-*
fi

claude plugin eval plugins --eval-dir "$plugin/evals-build" --trust-plugin --no-publish --scaffold \
  --output-dir "plugins/$plugin/evals/results/$(date -u +%Y-%m-%dT%H-%M-%SZ)" \
  --runs 1 --ablation none "${only[@]}" --judge-model sonnet \
  --allow-tools "${tools[@]}" "$@"
