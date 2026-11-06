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
for p in ai frontend backend progress dev core plan review ship; do dirs+=(--plugin-dir "$repo/plugins/$p"); done

# The OS sandbox blocks `git init` (.git) and any package that ships an `.idea/` dir (iconv-lite): its protected paths
# cannot be re-allowed, so a full scaffold needs SCAFFOLD_NO_SANDBOX=1 (run it yourself; the agent then has plain Bash as you).
settings='{"sandbox":{"enabled":true,"autoAllowBashIfSandboxed":true,"network":{"allowedDomains":["registry.npmjs.org","github.com","api.github.com","codeload.github.com","raw.githubusercontent.com"]}}}'
[ "${SCAFFOLD_NO_SANDBOX:-0}" = "1" ] && settings='{"sandbox":{"enabled":false}}'

cd "$work"
# `env -i` would drop the session's auth, so scrub by name instead: every variable that looks like a credential except
# Claude's own (ANTHROPIC_*, CLAUDE_CODE_*), so provider keys (OPENAI_API_KEY) and git-host tokens stay out of the agent.
scrub=()
while IFS= read -r name; do scrub+=(-u "$name"); done < <(env | cut -d= -f1 | grep -E 'TOKEN|SECRET|KEY|PASSWORD|CREDENTIAL|PASS$' | grep -vE '^(ANTHROPIC_|CLAUDE_CODE_)')
env ${scrub[@]+"${scrub[@]}"} CLAUDE_REPO_PROFILE=0 CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 claude -p "init codebase chatbot asisstant empty features for me using langchain framework and tracing with langfuse" \
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
eslint_deprecated() { grep -rqE '@typescript-eslint/no-deprecated' packages/config apps/agent/eslint.config.* --exclude-dir=node_modules; }
agent=apps/agent/src
four_sections() { grep -qE 'OVERVIEW' "$agent/prompts.ts" && grep -qE 'RESPONSE' "$agent/prompts.ts" && grep -qE 'OUT OF SCOPE' "$agent/prompts.ts" && grep -qE 'CONTEXT' "$agent/prompts.ts"; }
canary() { grep -q 'INTERNAL_CANARY_' "$agent/prompts.ts"; }
pii_on() { grep -qE '^PII_REDACTION=on[[:space:]]*$' .env.example; }
baseline_twelve() { [ "$(grep -cE '^\{.*\}[[:space:]]*$' apps/agent/evals/datasets/baseline.jsonl)" -eq 12 ]; }
list_reads_state() { grep -q 'getState' "$agent/server/threads.ts"; }
workspace() { [ -f pnpm-workspace.yaml ] && [ -f turbo.json ] && [ -d apps/web ] && [ -d apps/agent ] && [ -d packages/shared ] && [ -d packages/config ]; }
web_has_no_server() { ! grep -qE '"(hono|@hono/node-server|express|@copilotkit/runtime|@langchain/[^"]*|@mastra/[^"]*)"' apps/web/package.json; }
shared_used_by_both() { grep -rq '@repo/shared' apps/web/src --include='*.ts' --include='*.tsx' && grep -rq '@repo/shared' apps/agent/src --include='*.ts'; }
secrets_named() { grep -qE '^INTERNAL_API_TOKEN=(""|'"''"')?$' .env.example && grep -B1 -E '^INTERNAL_API_TOKEN=' .env.example | grep -q 'openssl rand'; }
agui_import() { grep -rq '@ag-ui/langgraph' apps/agent/src --include='*.ts'; }
no_framework_folder() { [ -f "$agent/server/main.ts" ] && [ ! -e "$agent/langchain" ] && [ ! -e "$agent/langgraph" ] && [ ! -e "$agent/mastra" ]; }
# eslint loads config the agent wrote, so it gets the same scrubbed env as the agent. It still runs outside the OS sandbox.
lint_agent_src() { [ -d node_modules ] && env ${scrub[@]+"${scrub[@]}"} pnpm --filter agent exec eslint src --max-warnings=0; }

check "monorepo: apps/web, apps/agent, packages/shared, packages/config" workspace
check "apps/web lists no server or agent framework package" web_has_no_server
check "both apps import @repo/shared" shared_used_by_both
check "no deprecated imports (@copilotkit/runtime/langgraph, hono/vercel)" no_deprecated_imports
check "LangGraphAgent imported from @ag-ui/langgraph" agui_import
check "the shared eslint preset enables @typescript-eslint/no-deprecated" eslint_deprecated
check "no agent folder named after the framework" no_framework_folder
check "eslint passes on apps/agent/src" lint_agent_src
check "$agent/prompts.ts has the four sections" four_sections
check "prompts.ts has an INTERNAL_CANARY_ line" canary
check ".env.example has PII_REDACTION=on" pii_on
check "apps/agent/evals/datasets/baseline.jsonl has 12 lines" baseline_twelve
check "thread list route reads the state of a stopped run" list_reads_state
check ".env.example names INTERNAL_API_TOKEN with how to generate it" secrets_named

[ "$fail" -eq 0 ] && echo "SCAFFOLD OK" || { echo "SCAFFOLD FAILED (log: $log; rerun with --keep to inspect $work)"; exit 1; }
