#!/usr/bin/env bash
# eval-plugin.sh — run a plugin's evals/ suite with real model calls (paid; not part of check.sh).
#   bash scripts/eval-plugin.sh ai                    # one cheap pass: 1 run per case, no baseline arm
#   bash scripts/eval-plugin.sh ai --runs 3 --ablation with-without      # full comparison before a demo
#   bash scripts/eval-plugin.sh ai --real-scaffold    # scaffold-* cases only, with offline pnpm and git in the sandbox (first argument)
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

# --real-scaffold: run only the scaffold-* cases (a real project; 2400 s per case in prompt.md), paid ~$12 per case on
# shape A (#194). The ceiling must cover the three cases, or the last graders go unscored.
# Without it those cases are dropped, so the cheap pass never grants the shell. The confined sandbox refuses every
# network host (CLAUDE_CODE_EVAL_CONFINED forces allowedDomains to []), so gh api fails there; it reads only the
# PATH bin dirs, so npm (a link into lib/) and `pnpm view` do not load. pnpm works offline: each case's
# warm/*/package.json is installed here, with network, into .eval-cache/pnpm, and the case's scaffold.sh clones that
# store into the sandbox HOME (scaffold-langchain). /usr/bin/git is the xcrun shim, which exits 72 there, and the
# agent's PATH ignores the sandbox HOME's shell files: git works only from a PATH dir ahead of /usr/bin outside
# /Users, such as /opt/homebrew/bin (`brew install git`), so the run stops before any paid call when there is none.
tools=("Bash(bash *preflight.sh*)" "Bash(python3 *)" "Bash(python *)" Write Edit)
only=(--concurrency 4 --max-cost-usd 6)
if [ "${1:-}" = "--real-scaffold" ]; then
  shift
  tools+=("Bash(pnpm *)" "Bash(npm *)" "Bash(npx *)" "Bash(node *)" "Bash(git *)" "Bash(gh api *)" "Bash(mkdir *)" "Bash(ls *)" "Bash(cat *)" "Bash(grep *)")
  only=(--case 'scaffold-*' --concurrency 1 --max-cost-usd 45)
  case "$(command -v git)" in
    /usr/bin/git | /Users/*) echo "--real-scaffold needs git ahead of /usr/bin outside /Users (brew install git)" >&2; exit 1 ;;
  esac
  cache="$PWD/.eval-cache/pnpm"
  for manifest in "$build"/scaffold-*/warm/*/package.json; do
    [ -f "$manifest" ] || continue
    warm="$(mktemp -d)"
    cp "$manifest" "$warm/"
    (cd "$warm" && pnpm install --ignore-scripts --store-dir "$cache/store" --cache-dir "$cache/metadata" \
      --config.manage-package-manager-versions=false --reporter=append-only | tail -3)
    rm -rf "$warm"
  done
else
  rm -rf "$build"/scaffold-*
fi

claude plugin eval plugins --eval-dir "$plugin/evals-build" --trust-plugin --no-publish --scaffold \
  --output-dir "plugins/$plugin/evals/results/$(date -u +%Y-%m-%dT%H-%M-%SZ)" \
  --runs 1 --ablation none "${only[@]}" --judge-model sonnet \
  --allow-tools "${tools[@]}" "$@"
