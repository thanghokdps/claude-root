#!/usr/bin/env bash
# preflight.sh — what a blank machine is missing before an agent repo can be scaffolded and run one real turn.
# Reports only: never installs, never prints a key's value. Always exits 0; the report is the result.
#   bash preflight.sh [project-dir]
dir="${1:-.}"
missing=0
os="$(uname -s)"

hint() {  # install hint for this OS
  case "$os:$1" in
    Darwin:node) echo "brew install node@22  (or: nvm install 22)" ;;
    Darwin:git)  echo "xcode-select --install  (or: brew install git)" ;;
    Darwin:pnpm) echo "corepack enable pnpm  (ships with Node ≥ 16.13)" ;;
    Linux:node)  echo "nvm install 22  (https://github.com/nvm-sh/nvm)" ;;
    Linux:git)   echo "sudo apt-get install -y git" ;;
    Linux:pnpm)  echo "corepack enable pnpm" ;;
    *:node)      echo "install Node.js 22 LTS from https://nodejs.org" ;;
    *:git)       echo "install git from https://git-scm.com" ;;
    *:pnpm)      echo "corepack enable pnpm" ;;
  esac
}

row() { printf '%-18s %-8s %s\n' "$1" "$2" "$3"; }

echo "Preflight — $(cd "$dir" 2>/dev/null && pwd || echo "$dir")"
row "CHECK" "STATUS" "DETAIL"

if command -v git >/dev/null 2>&1; then row git ok "$(git --version | awk '{print $3}')"
else row git MISSING "$(hint git)"; missing=$((missing + 1)); fi

if command -v node >/dev/null 2>&1; then
  major="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
  if [ "$major" -ge 20 ]; then row node ok "$(node --version)"
  else row node OLD "$(node --version) — LangGraph.js and CopilotKit need ≥ 20; $(hint node)"; missing=$((missing + 1)); fi
else row node MISSING "$(hint node)"; missing=$((missing + 1)); fi

pm=""
for p in pnpm npm yarn bun; do command -v "$p" >/dev/null 2>&1 && { pm="$p"; break; }; done
for lock in pnpm-lock.yaml:pnpm yarn.lock:yarn bun.lockb:bun package-lock.json:npm; do
  [ -f "$dir/${lock%%:*}" ] && { pm="${lock##*:}"; break; }
done
if [ -n "$pm" ] && command -v "$pm" >/dev/null 2>&1; then row "package manager" ok "$pm $("$pm" --version 2>/dev/null)"
else row "package manager" MISSING "$(hint pnpm)"; missing=$((missing + 1)); fi

# A real turn needs one model key. Presence only — the value is never read into output.
key=""
for k in ANTHROPIC_API_KEY OPENAI_API_KEY GOOGLE_API_KEY AZURE_OPENAI_API_KEY; do
  if [ -n "${!k:-}" ]; then key="$k (env)"; break; fi
  for f in "$dir/.env" "$dir/.env.local"; do
    [ -f "$f" ] && grep -qE "^${k}=.+" "$f" && { key="$k ($(basename "$f"))"; break 2; }
  done
done
if [ -n "$key" ]; then row "model key" ok "$key"
else row "model key" MISSING "set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env (gitignored) — needed for the first real turn"; missing=$((missing + 1)); fi

if [ -d "$dir/.git" ] || git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then row "git repo" ok "initialised"
else row "git repo" MISSING "git init (scaffold commits need a repo)"; missing=$((missing + 1)); fi

echo "missing: $missing"
exit 0
