#!/usr/bin/env bash
# check.sh — every free, deterministic kit check. Run before committing; CI runs the same.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 scripts/lint-kit.py
python3 scripts/eval-triggers.py
if command -v claude >/dev/null 2>&1; then
  claude plugin validate .
fi
