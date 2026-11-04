#!/usr/bin/env bash
# preflight.sh — what a blank machine is missing before an agent repo can be scaffolded and run one real turn.
# Reports only: never installs, never prints a key's value. Always exits 0; the report is the result.
#   bash preflight.sh [project-dir] [openai|anthropic|google|azure]   (provider defaults to openai)
dir="${1:-.}"
provider="${2:-openai}"
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
  # The scaffold's test runner sets the floor (vitest 5.1.0 engines), above LangGraph.js and CopilotKit's own ≥ 20.
  read -r major minor < <(node -p 'process.versions.node.split(".").slice(0, 2).join(" ")' 2>/dev/null || echo "0 0")
  if { [ "$major" -eq 22 ] && [ "$minor" -ge 12 ]; } || [ "$major" -eq 24 ] || [ "$major" -ge 26 ]; then row node ok "$(node --version)"
  else row node OLD "$(node --version) — the test runner needs ^22.12.0, ^24.0.0 or >=26.0.0; $(hint node)"; missing=$((missing + 1)); fi
else row node MISSING "$(hint node)"; missing=$((missing + 1)); fi

pm=""
for p in pnpm npm yarn bun; do command -v "$p" >/dev/null 2>&1 && { pm="$p"; break; }; done
for lock in pnpm-lock.yaml:pnpm yarn.lock:yarn bun.lockb:bun package-lock.json:npm; do
  [ -f "$dir/${lock%%:*}" ] && { pm="${lock##*:}"; break; }
done
if [ -n "$pm" ] && command -v "$pm" >/dev/null 2>&1; then row "package manager" ok "$pm $("$pm" --version 2>/dev/null)"
else row "package manager" MISSING "$(hint pnpm)"; missing=$((missing + 1)); fi

# A real turn needs the chosen provider's key in the project's own .env. Presence only — the value is never
# read into output. The shell env is not read: Claude Code's own ANTHROPIC_API_KEY must not pick the app's provider.
case "$provider" in
  openai) k=OPENAI_API_KEY ;; anthropic) k=ANTHROPIC_API_KEY ;; google) k=GOOGLE_API_KEY ;; azure) k=AZURE_OPENAI_API_KEY ;;
  *) k="" ;;
esac
is_set() {  # $1 variable, $2 env file: a NAME=<value> line whose value is not empty ("", '' and a bare comment count as empty)
  grep -qE "^$1=" "$2" && ! grep -qE "^$1=(\"\"|'')?[[:space:]]*(#.*)?$" "$2"
}
key=""
for f in "$dir/.env" "$dir/.env.local"; do
  [ -n "$k" ] && [ -f "$f" ] && is_set "$k" "$f" && { key="$k ($(basename "$f"))"; break; }
done
if [ -z "$k" ]; then row "model key" MISSING "unknown provider '$provider' — use openai, anthropic, google or azure"; missing=$((missing + 1))
elif [ -n "$key" ]; then row "model key" ok "$key"
else row "model key" MISSING "set $k in .env (gitignored) — needed for the first real turn"; missing=$((missing + 1)); fi

# Every variable .env.example leaves empty is a secret the user fills by hand (the internal token, tracing keys…):
# one row per missing one, with the comment the scaffold wrote above it, so the user gets a step and not a boot error.
# A tracing provider's keys are named but not counted while TRACING_PROVIDER does not select it: the app boots without them.
# Before the scaffold there is no .env.example, and only the provider's key above applies.
ex="$dir/.env.example"
tracing="$(sed -nE "s/^TRACING_PROVIDER=[\"']?([a-z]*).*/\1/p" "$dir/.env" "$dir/.env.local" "$ex" 2>/dev/null | head -1)"
tracing_key_off() {
  case "$1" in
    LANGFUSE_*) [ "$tracing" != langfuse ] ;;
    LANGSMITH_*) [ "$tracing" != langsmith ] ;;
    *) return 1 ;;
  esac
}
secret_hint() {  # the comment on the line above the variable in .env.example, else a default by name
  # Repo text, shown and never run: plain characters only, 80 at most, labelled with its source.
  local c
  c="$(grep -B1 -E "^$1=" "$ex" | head -1 | sed -nE 's/^#[[:space:]]*//p' | tr -cd 'A-Za-z0-9 ._:/@=+-' | cut -c1-80)"
  [ -n "$c" ] && { echo ".env.example says: $c"; return; }
  case "$1" in
    INTERNAL_API_TOKEN) echo "generate: openssl rand -base64 48" ;;
    *) echo "fill from the service that issues it" ;;
  esac
}
if [ -f "$ex" ]; then
  total=0; filled=0
  while IFS= read -r name; do
    [ "$name" = "$k" ] && continue   # reported as "model key" above
    set_in=""
    for f in "$dir/.env" "$dir/.env.local"; do
      [ -f "$f" ] && is_set "$name" "$f" && { set_in="$f"; break; }
    done
    if [ -n "$set_in" ]; then total=$((total + 1)); filled=$((filled + 1))
    elif tracing_key_off "$name"; then row "$name" optional "only when TRACING_PROVIDER selects it — $(secret_hint "$name")"
    else total=$((total + 1)); row "$name" MISSING "set in .env — $(secret_hint "$name")"; missing=$((missing + 1)); fi
  done < <(grep -oE "^[A-Za-z_][A-Za-z0-9_]*=(\"\"|'')?$" "$ex" | cut -d= -f1)
  [ "$total" -gt 0 ] && [ "$filled" -eq "$total" ] && row secrets ok "$filled of $total set (.env.example)"
fi

if [ -d "$dir/.git" ] || git -C "$dir" rev-parse --git-dir >/dev/null 2>&1; then row "git repo" ok "initialised"
else row "git repo" MISSING "git init (scaffold commits need a repo)"; missing=$((missing + 1)); fi

echo "missing: $missing"
exit 0
