# 0002 — Every plugin stays at 1.0.0 until the kit is published

**Status:** Accepted (27 Oct 2026)

## Context

Bumping a plugin's `version` on every change caused merge conflicts on `plugin.json` across parallel PRs and noise in every diff, while only the kit's author had the plugins installed.

## Decision

Every `plugin.json` stays at `1.0.0` until the kit is published. The commit on `main` identifies the kit a document describes. A changed kit reaches a machine by `/plugin marketplace update harness` (or `bash scripts/install.sh`, which uninstalls and reinstalls every plugin, since an unchanged version keeps the old cached copy).

## Consequences

- No version conflicts between PRs; a reviewer reads the commit, not a version.
- `/plugin update` cannot tell an old copy from a new one by version alone, so the update step above is required after a merge.
- Once published, versions are bumped per changed plugin and tagged `<plugin>--v<version>` (CLAUDE.md § Release).

## Where

`plugins/*/.claude-plugin/plugin.json`, `CLAUDE.md` § Versions.
