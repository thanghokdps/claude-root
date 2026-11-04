#!/usr/bin/env bash
# stale-install.sh — say when the installed kit is behind the marketplace clone. Trigger: SessionStart.
# Every plugin stays at 1.0.0, so `claude plugin update` sees no change and the cached copy silently ages;
# only scripts/install.sh refreshes it. Reads local files only, never the network. Non-blocking.
# Any missing file or value raises inside python and stderr is dropped, which is the "stay quiet" path.
python3 -I - 2>/dev/null <<'PY'
import json, os, subprocess

plugins = os.path.expanduser("~/.claude/plugins")
with open(os.path.join(plugins, "known_marketplaces.json")) as f:
    marketplace = json.load(f)["harness"]
if marketplace["source"]["source"] == "directory":  # a Folder source is loaded in place, it cannot be stale
    raise SystemExit
with open(os.path.join(plugins, "installed_plugins.json")) as f:
    entries = json.load(f)["plugins"]["core@harness"]
# install.sh rewrites the user entry; project entries keep the sha of their last install, while all scopes
# share one cached copy, so they say nothing about what is running.
entry = max(entries, key=lambda e: (e.get("scope") == "user", e.get("lastUpdated", "")))
installed = entry["gitCommitSha"]
head = subprocess.run(["git", "-C", marketplace["installLocation"], "rev-parse", "HEAD"],
                      capture_output=True, text=True, timeout=5, check=True).stdout.strip()
if installed != head:
    context = (f"STALE HARNESS INSTALL: plugins are at {installed[:8]}, the marketplace has {head[:8]}. "
               "Tell the user to run `bash scripts/install.sh` from a kit checkout, then start a new session.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))
PY
exit 0
