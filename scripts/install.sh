#!/usr/bin/env bash
# install.sh — install harness for the current user. Idempotent; re-run after pulling the kit.
#
#   1. Back up ~/.claude/CLAUDE.md, rules/, settings.json and the skills this kit replaces
#   2. Install global/CLAUDE.md and rules/*.md (the only always-loaded files)
#   3. Register this directory as a local marketplace and install the harness bundle, which
#      pulls in every role plugin as a dependency (copied to the plugin cache — re-run after edits)
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
claude plugin marketplace add "$KIT" >/dev/null 2>&1 || true
claude plugin marketplace update harness >/dev/null 2>&1 || true
# Each plugin explicitly: `plugin update` does not install dependencies a new version adds, and
# re-running `install` on an installed bundle adds only one missing dependency per run (CLI 2.1.305).
claude plugin update harness@harness >/dev/null 2>&1 || true
for p in $(python3 -c "import json,sys; print(' '.join(p['name'] for p in json.load(open(sys.argv[1]))['plugins']))" "$KIT/.claude-plugin/marketplace.json"); do
  claude plugin install "$p@harness" >/dev/null 2>&1 || echo "  install failed: $p@harness (run: claude plugin install $p@harness)"
done
# The CLI's own message quotes a stale recorded version; folderVersion is what loads in place.
claude plugin list --json 2>/dev/null | python3 -c '
import json, sys
seen = {}
for p in json.load(sys.stdin):
    if p["id"].endswith("@harness"):
        seen[p["id"].split("@")[0]] = p.get("folderVersion") or p.get("version")
print("  plugins: " + ", ".join(f"{n} {v}" for n, v in sorted(seen.items())))
' || true

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
