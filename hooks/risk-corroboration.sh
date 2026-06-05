#!/bin/bash

# PreToolUse hook: block git commit when staged diff trips a hard-gate signal
# but the declared Lane in specs/<slug>/SUMMARY.md is below high-risk.
# Exits 0 to allow, 2 to block.

INPUT=$(cat /dev/stdin)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

echo "$COMMAND" | grep -qE '^git commit' || exit 0

REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_DIR" ] && exit 0
cd "$REPO_DIR" || exit 0

STAGED_PATHS=$(git diff --cached --name-only 2>/dev/null || true)
[ -z "$STAGED_PATHS" ] && exit 0

# Added code lines only — exclude prose, hooks, specs
CODE_ADDED=$(git diff --cached -U0 -- . ':!*.md' ':!docs/' ':!specs/' ':!hooks/' ':!.claude/' 2>/dev/null \
  | grep -E '^\+[^+]' || true)

CODE_REMOVED=$(git diff --cached -U0 -- . ':!*.md' ':!docs/' ':!specs/' ':!hooks/' ':!.claude/' 2>/dev/null \
  | grep -E '^-[^-]' || true)

TRIPPED=""
add_cat() { TRIPPED="$TRIPPED $1"; }

# Path-based categories
echo "$STAGED_PATHS" | grep -qE '(^|/)settings\.json$|(^|/)hooks/' && add_cat "high-blast"
echo "$STAGED_PATHS" | grep -qE '(^|/)(migrations?|alembic)/' && add_cat "data-loss/migration"
echo "$STAGED_PATHS" | grep -qE '(^|/)(requirements[^/]*\.txt|package\.json|pyproject\.toml|go\.mod|Gemfile)$' && add_cat "external-provider"

# Keyword categories (added lines)
echo "$CODE_ADDED" | grep -qiE '(login|logout|\bsession\b|jwt|password|refresh_token|oauth|set_cookie|bcrypt|hashpw)' && add_cat "auth"
echo "$CODE_ADDED" | grep -qiE '(\brole\b|permission|is_admin|require_role|authorize|rbac|access_control)' && add_cat "authorization"
echo "$CODE_ADDED" | grep -qiE '(audit_log|access_log|encrypt|decrypt|\bpii\b|sensitive_data)' && add_cat "audit/security"
echo "$CODE_ADDED" | grep -qiE '(stripe|twilio|sendgrid|boto3|paypal|\bwebhook)' && add_cat "external-provider"
echo "$CODE_ADDED" | grep -qiE '(DROP TABLE|DELETE FROM|TRUNCATE|ALTER TABLE|op\.drop|drop_table|drop_column)' && add_cat "data-loss/migration"
echo "$CODE_REMOVED" | grep -qiE '(assert |validator|required=True|\braise )' && add_cat "weakening-validation"

TRIPPED=$(echo "$TRIPPED" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' ')
[ -z "$TRIPPED" ] && exit 0

# Resolve the declared Lane from specs/*/SUMMARY.md
LANE=""
for f in $(echo "$STAGED_PATHS" | grep -E '(^|/)SUMMARY\.md$' || true); do
  L=$(git show ":$f" 2>/dev/null | grep -iE '^Lane:' | head -1)
  [ -n "$L" ] && LANE="$L" && break
done

if [ -z "$LANE" ]; then
  RECENT=$(ls -t specs/*/SUMMARY.md 2>/dev/null | head -1)
  [ -n "$RECENT" ] && LANE=$(grep -iE '^Lane:' "$RECENT" | head -1)
fi

LANE_VAL=$(echo "$LANE" | tr 'A-Z' 'a-z' | grep -oE 'tiny|normal|high-risk' | head -1)

if [ "$LANE_VAL" = "high-risk" ]; then
  echo "[RISK CORROBORATION] hard-gate signals ($TRIPPED) corroborated by Lane: high-risk — OK." >&2
  exit 0
fi

if [ -n "$LANE_VAL" ]; then
  echo "[RISK CORROBORATION] BLOCKED." >&2
  echo " Staged diff trips hard-gate categories: $TRIPPED" >&2
  echo " But SUMMARY.md declares Lane: $LANE_VAL (below high-risk)." >&2
  echo " Re-run /coordinator and set Lane: high-risk, or narrow the scope." >&2
  exit 2
fi

# No declared Lane
echo "[RISK CORROBORATION] WARNING — hard-gate signals ($TRIPPED) with no declared Lane." >&2
echo " Run /coordinator to classify this work and record a Lane in specs/<slug>/SUMMARY.md." >&2
exit 0
