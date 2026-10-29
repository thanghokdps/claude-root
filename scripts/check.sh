#!/usr/bin/env bash
# check.sh — every free, deterministic kit check. Run before committing; CI runs the same.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 scripts/test_lint_kit.py
python3 scripts/test_skill_progress.py
python3 scripts/test_branch_guard.py
python3 scripts/test_edit_guard.py
python3 scripts/test_ticket_gate.py
python3 scripts/test_secret_guard.py
python3 scripts/test_repo_profile.py
python3 scripts/test_test_lock.py
python3 scripts/test_weakened_check.py
python3 scripts/test_release_gate.py
python3 scripts/test_compare_shots.py
python3 scripts/test_text_styles.py
python3 scripts/test_check_ui.py
python3 scripts/test_sync_remote.py
python3 scripts/test_run_evidence.py
python3 scripts/test_thunderkds_hooks.py
python3 scripts/test_learn_capture.py
python3 scripts/test_learn_promote.py
python3 scripts/lint-kit.py
python3 scripts/eval-triggers.py
if command -v claude >/dev/null 2>&1; then
  claude plugin validate .
  for p in plugins/*/; do claude plugin validate "$p" >/dev/null || { claude plugin validate "$p"; exit 1; }; done
  echo "plugin validate: marketplace + $(ls -d plugins/*/ | wc -l | tr -d ' ') plugins passed"
fi
