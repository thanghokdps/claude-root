#!/usr/bin/env bash
# install.sh — install harness for the current user. Idempotent; re-run after pulling the kit.
#
#   1. Back up ~/.claude/CLAUDE.md, rules/, settings.json and the skills this kit replaces
#   2. Install global/CLAUDE.md and rules/*.md (the only always-loaded files)
#   3. Register this directory as a local marketplace (unless `harness` is already registered from
#      another source, e.g. GitLab, which is kept) and install every plugin into the plugin cache
#   4. Migrate from the old copy-based install: move kit skills out of ~/.claude/skills and
#      drop kit hook registrations from ~/.claude/settings.json (the plugin registers them now)
#
# Undo: restore from the printed backup dir, then `claude plugin uninstall harness && claude plugin prune`.
set -euo pipefail

KIT="$(cd "$(dirname "$0")/.." && pwd)"
G="$HOME/.claude"
B="$G/backups/harness-install-$(date +%Y%m%d-%H%M%S)"
RULES="$KIT/plugins/core/rules"
mkdir -p "$B/skills" "$B/rules" "$G/rules"

echo "harness installer — kit: $KIT"

# 1. Backup
cp "$G/CLAUDE.md" "$B/" 2>/dev/null || true
cp "$G/settings.json" "$B/" 2>/dev/null || true
cp "$G"/rules/*.md "$B/rules/" 2>/dev/null || true

# 2. Always-loaded instructions. Rules no longer shipped here move to the backup, not the bin.
cp "$KIT/global/CLAUDE.md" "$G/CLAUDE.md"
for r in "$G"/rules/*.md; do
  [ -f "$r" ] || continue
  [ -f "$RULES/$(basename "$r")" ] || mv "$r" "$B/rules/$(basename "$r").retired"
done
cp "$RULES"/*.md "$G/rules/"
echo "  CLAUDE.md + rules: $(ls "$RULES"/*.md | wc -l | tr -d ' ') rule files"

# 3. Plugin
command -v claude >/dev/null || { echo "claude CLI not found"; exit 1; }
# Before 4.0 the marketplace was `thang-kit` with `thang-<role>` plugins; the same directory cannot be registered twice.
if claude plugin marketplace list 2>/dev/null | grep -q "thang-kit"; then
  for p in thang-kit thang-guards thang-lead thang-agent thang-ship thang-dev thang-review thang-plan thang-core thang-progress; do
    claude plugin uninstall "$p@thang-kit" >/dev/null 2>&1 || true
  done
  claude plugin marketplace remove thang-kit >/dev/null 2>&1 || true
  echo "  migrated: removed thang-kit marketplace and thang-* plugins"
fi
# A team install registers `harness` from GitLab; adding this directory over it fails (the source must
# match the user's extraKnownMarketplaces entry), so keep that source and only update it.
SOURCE=$(claude plugin marketplace list 2>/dev/null | awk '/❯ harness$/ {getline; sub(/^ *Source: */, ""); print; exit}')
if [ -z "$SOURCE" ]; then
  claude plugin marketplace add "$KIT" >/dev/null 2>&1 || true
  SOURCE="Folder ($KIT)"
fi
claude plugin marketplace update harness >/dev/null 2>&1 || echo "  marketplace update failed (VPN off?) — installing from the last fetched copy"
echo "  plugins from: $SOURCE"
case "$SOURCE" in Folder*) ;; *) echo "  local edits in $KIT reach this install only after push + /sync-remote" ;; esac
# Each plugin explicitly: `plugin update` does not install dependencies a new version adds, and
# re-running `install` on an installed bundle adds only one missing dependency per run (CLI 2.1.305).
# Versions stay at 1.0.0 until the kit is published, so `plugin update` sees no change and keeps the
# old cached copy: uninstall every plugin (dependents first, reverse marketplace order), then install fresh.
PLUGINS=$(python3 -c "import json,sys; print(' '.join(p['name'] for p in json.load(open(sys.argv[1]))['plugins']))" "$KIT/.claude-plugin/marketplace.json")
for p in $(printf '%s\n' $PLUGINS | tail -r 2>/dev/null || printf '%s\n' $PLUGINS | tac); do
  claude plugin uninstall "$p@harness" >/dev/null 2>&1 || true
done
claude plugin prune >/dev/null 2>&1 || true
# The CLI's own line can name the version that was installed before this run, so print the kit's
# versions instead and show CLI output only when an install fails.
for p in $PLUGINS; do
  out=$(claude plugin install "$p@harness" 2>&1) || echo "  $p: install failed — $(printf '%s' "$out" | tail -1)"
done
# Role and domain packs stay off at user scope: core's repo-profile hook enables them per repo when it detects
# their stack or domain (frontend: react/next/vue/svelte; backend: a server framework, an ORM, go or rust;
# mobile: react-native / expo / eas.json; devops: Dockerfile, compose, CI workflow, *.tf, k8s/, Chart.yaml;
# ai: @langchain/@copilotkit/@mastra/langgraph; workplace: a `Domain: workplace` line or HR module folders),
# so other repos don't carry their skills.
for p in frontend backend mobile devops ai workplace; do
  out=$(claude plugin disable "$p@harness" --scope user 2>&1) || true
  case "$out" in *Failed*) echo "  WARN $p stays on at user scope — $(printf '%s' "$out" | head -1)" ;; esac
done
echo "  packs off at user scope (enabled per repo by repo-profile): frontend backend mobile devops ai workplace"
echo "  plugins: $(for f in "$KIT"/plugins/*/.claude-plugin/plugin.json; do
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(f\"{d['name']} {d['version']}\", end=' ')" "$f"; done)"

# A kit kept on two remotes (GitHub + GitLab) can drift: say so before the user installs a stale copy.
if git -C "$KIT" rev-parse --git-dir >/dev/null 2>&1 && [ "$(git -C "$KIT" remote | wc -l)" -ge 2 ]; then
  heads=$(for r in $(git -C "$KIT" remote); do
    printf '%s %s\n' "$r" "$(git -C "$KIT" ls-remote "$r" HEAD 2>/dev/null | cut -c1-12)"; done)
  if [ "$(printf '%s\n' "$heads" | awk '$2 != "" {print $2}' | sort -u | wc -l)" -gt 1 ]; then
    echo "  ⚠️  the kit's remotes point at different commits:"; printf '%s\n' "$heads" | sed 's/^/    /'
    echo "     Bring them in line with /sync-remote (ship) before installing on another machine."
  fi
fi

# 4. Migrate old copies: plugin skills would otherwise show up twice.
for d in "$KIT"/plugins/*/skills/*/; do
  s="$(basename "$d")"
  [ -d "$G/skills/$s" ] && mv "$G/skills/$s" "$B/skills/$s"
done
for s in code-review figma-to-screen gen-tests verify-feature; do   # renamed or moved to stacks/
  [ -d "$G/skills/$s" ] && mv "$G/skills/$s" "$B/skills/$s"
done
python3 - "$G/settings.json" "$KIT/plugins/guards/hooks" <<'PY'
import json, os, sys
path, hooks_dir = sys.argv[1], sys.argv[2]
if not os.path.exists(path):
    sys.exit(0)
kit_hooks = {f for f in os.listdir(hooks_dir) if f.endswith(".sh")}
s = json.load(open(path))
removed = 0
for event, matchers in list(s.get("hooks", {}).items()):
    kept = []
    for m in matchers:
        hs = [h for h in m.get("hooks", []) if os.path.basename(h.get("command", "").split()[0]) not in kit_hooks]
        removed += len(m.get("hooks", [])) - len(hs)
        if hs:
            kept.append({**m, "hooks": hs})
    if kept:
        s["hooks"][event] = kept
    else:
        del s["hooks"][event]
json.dump(s, open(path, "w"), indent=2, ensure_ascii=False)
open(path, "a").write("\n")
print(f"  settings.json: removed {removed} kit hook registration(s) now owned by the plugin")
PY

echo "Backup: $B"
echo "Open a new session to load the changes. Optional: bash $KIT/scripts/setup-mcp.sh"
