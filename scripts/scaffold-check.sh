#!/usr/bin/env bash
# scaffold-check.sh — run the LangChain skeleton request for real and check the files it leaves (paid, ~$1-3, 10-15 min).
#   bash scripts/scaffold-check.sh [--keep]
# `claude plugin eval` cannot do this: its sandbox has no git and no network (PR "scaffold-langchain" run, 2026-11-02),
# so the agent here runs as a normal headless session in a temp dir, with the ai plugin and its dependencies loaded.
# Trust: Bash is allowed but runs in Claude Code's OS sandbox (writes confined to the temp dir, network only to the npm
# registry and GitHub), with no git-host tokens in the env. A narrow Bash prefix list would deny compound commands
# such as `cd x; for ...`.
# The agent cannot write .env (secret guard), so the run ends before the first real chat turn; files are checked as they stand.
set -uo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
log="$work/.agent.log"
[ "${1:-}" = "--keep" ] || trap 'rm -rf "$work"' EXIT

dirs=()
for p in ai progress dev core plan review ship; do dirs+=(--plugin-dir "$repo/plugins/$p"); done

# The OS sandbox blocks `git init` (.git) and any package that ships an `.idea/` dir (iconv-lite): its protected paths
# cannot be re-allowed, so a full scaffold needs SCAFFOLD_NO_SANDBOX=1 (run it yourself; the agent then has plain Bash as you).
settings='{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"network":{"allowedDomains":["registry.npmjs.org","github.com","api.github.com","codeload.github.com","raw.githubusercontent.com"]}}}'
[ "${SCAFFOLD_NO_SANDBOX:-0}" = "1" ] && settings='{"sandbox":{"enabled":false}}'

cd "$work"
env -u GH_TOKEN -u GITHUB_TOKEN -u GITLAB_TOKEN CLAUDE_REPO_PROFILE=0 claude -p "init codebase chatbot asisstant empty features for me using langchain framework and tracing with langfuse" \
  "${dirs[@]}" --model sonnet --max-budget-usd 5 --output-format json \
  --permission-mode dontAsk \
  --settings "$settings" \
  --allowedTools Read Write Edit Glob Grep Skill Bash \
  --disallowedTools AskUserQuestion "Bash(sudo:*)" "Bash(rm -rf /*)" "Bash(rm -rf ~*)" > "$log" 2>&1
echo "agent exit $? ; cost: $(python3 -c "import json;print(json.load(open('$log')).get('total_cost_usd'))" 2>/dev/null)"

fail=0
check() { # check <label> <command...>
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "PASS $label"; else echo "FAIL $label"; fail=1; fi
}
no_deprecated_imports() { ! grep -rEq '@copilotkit/runtime/langgraph|hono/vercel' . --include='*.ts' --include='*.tsx' --include='*.json' --exclude-dir=node_modules --exclude-dir=.git; }
eslint_deprecated() { grep -qE '@typescript-eslint/no-deprecated' eslint.config.*; }
four_sections() { grep -qE 'OVERVIEW' src/langchain/prompts.ts && grep -qE 'RESPONSE' src/langchain/prompts.ts && grep -qE 'OUT OF SCOPE' src/langchain/prompts.ts && grep -qE 'CONTEXT' src/langchain/prompts.ts; }
canary() { grep -q 'INTERNAL_CANARY_' src/langchain/prompts.ts; }
pii_off() { grep -qE '^PII_REDACTION=off[[:space:]]*$' .env.example; }
baseline_four() { [ "$(grep -cE '^\{.*\}[[:space:]]*$' evals/datasets/baseline.jsonl)" -eq 4 ]; }
agui_import() { grep -rq '@ag-ui/langgraph' src --include='*.ts'; }
lint_agent_folder() { [ -d node_modules ] && npx eslint src/langchain --max-warnings=0; }

check "no deprecated imports (@copilotkit/runtime/langgraph, hono/vercel)" no_deprecated_imports
check "LangGraphAgent imported from @ag-ui/langgraph" agui_import
check "eslint.config.* enables @typescript-eslint/no-deprecated" eslint_deprecated
check "eslint passes on src/langchain" lint_agent_folder
check "src/langchain/prompts.ts has the four sections" four_sections
check "prompts.ts has an INTERNAL_CANARY_ line" canary
check ".env.example has PII_REDACTION=off" pii_off
check "evals/datasets/baseline.jsonl has 4 lines" baseline_four

[ "$fail" -eq 0 ] && echo "SCAFFOLD OK" || { echo "SCAFFOLD FAILED (log: $log; rerun with --keep to inspect $work)"; exit 1; }
