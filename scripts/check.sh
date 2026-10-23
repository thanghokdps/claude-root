#!/usr/bin/env bash
# check.sh — every free, deterministic kit check. Run before committing; CI runs the same.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 scripts/test_lint_kit.py
python3 scripts/test_skill_progress.py
python3 scripts/test_branch_guard.py
python3 scripts/test_compare_shots.py
python3 scripts/lint-kit.py
python3 scripts/eval-triggers.py
if command -v claude >/dev/null 2>&1; then
  claude plugin validate .
  for p in plugins/*/; do claude plugin validate "$p" >/dev/null || { claude plugin validate "$p"; exit 1; }; done
  echo "plugin validate: marketplace + $(ls -d plugins/*/ | wc -l | tr -d ' ') plugins passed"
fi
