#!/usr/bin/env bash
# install.sh — install thang-kit for the current user. Idempotent; re-run after pulling the kit.
#
#   1. Back up ~/.claude/CLAUDE.md, rules/, settings.json and the skills this kit replaces
#   2. Install global/CLAUDE.md and rules/*.md (the only always-loaded files)
#   3. Register this directory as a local marketplace and install the thang-kit plugin
#      (skills, hooks, references load in place from here — edit the kit, changes are live)
#   4. Migrate from the old copy-based install: move kit skills out of ~/.claude/skills and
#      drop kit hook registrations from ~/.claude/settings.json (the plugin registers them now)
#
# Undo: restore from the printed backup dir, then `claude plugin uninstall thang-kit`.
set -euo pipefail

KIT="$(cd "$(dirname "$0")/.." && pwd)"
G="$HOME/.claude"
B="$G/backups/thang-kit-install-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$B/skills" "$B/rules" "$G/rules"

echo "thang-kit installer — kit: $KIT"

# 1. Backup
cp "$G/CLAUDE.md" "$B/" 2>/dev/null || true
cp "$G/settings.json" "$B/" 2>/dev/null || true
cp "$G"/rules/*.md "$B/rules/" 2>/dev/null || true

# 2. Always-loaded instructions. Rules no longer shipped here move to the backup, not the bin.
cp "$KIT/global/CLAUDE.md" "$G/CLAUDE.md"
for r in "$G"/rules/*.md; do
  [ -f "$r" ] || continue
  [ -f "$KIT/rules/$(basename "$r")" ] || mv "$r" "$B/rules/$(basename "$r").retired"
done
cp "$KIT"/rules/*.md "$G/rules/"
echo "  CLAUDE.md + rules: $(ls "$KIT"/rules/*.md | wc -l | tr -d ' ') rule files"

# 3. Plugin
command -v claude >/dev/null || { echo "claude CLI not found"; exit 1; }
claude plugin marketplace add "$KIT" >/dev/null 2>&1 || true
claude plugin install thang-kit@thang-kit 2>&1 | tail -1

# 4. Migrate old copies: plugin skills would otherwise show up twice.
for d in "$KIT"/skills/*/; do
  s="$(basename "$d")"
  [ -d "$G/skills/$s" ] && mv "$G/skills/$s" "$B/skills/$s"
done
for s in code-review figma-to-screen gen-tests verify-feature; do   # renamed or moved to stacks/
  [ -d "$G/skills/$s" ] && mv "$G/skills/$s" "$B/skills/$s"
done
python3 - "$G/settings.json" "$KIT/hooks" <<'PY'
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
