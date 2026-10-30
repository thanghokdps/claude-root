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
python3 scripts/test_ask_once.py
python3 scripts/test_guards_cwd.py
python3 scripts/test_session_handoff.py
python3 scripts/test_init_standalone.py
python3 scripts/test_release_gate.py
python3 scripts/test_infra_gate.py
python3 scripts/test_compare_shots.py
python3 scripts/test_text_styles.py
python3 scripts/test_check_ui.py
python3 scripts/test_sync_remote.py
python3 scripts/test_run_evidence.py
python3 scripts/test_thunderkds_hooks.py
python3 scripts/test_learn_capture.py
python3 scripts/test_learn_promote.py
python3 scripts/test_check_upstream.py
python3 scripts/test_build_site.py
python3 scripts/test_skill_map.py
python3 scripts/lint-kit.py
python3 scripts/eval-triggers.py
if python3 -c "import pytest, yaml" 2>/dev/null; then
  (cd eval && python3 -m pytest -q tests)
else
  echo "eval/tests skipped: pip install -r eval/requirements.txt" >&2
fi
if command -v claude >/dev/null 2>&1; then
  claude plugin validate .
  for p in plugins/*/; do claude plugin validate "$p" >/dev/null || { claude plugin validate "$p"; exit 1; }; done
  echo "plugin validate: marketplace + $(ls -d plugins/*/ | wc -l | tr -d ' ') plugins passed"
fi
