# ship

Land and release: finish-branch, ci-triage, release-checklist, write-migration.

## Install

```
/plugin marketplace add thanghokdps/claude-root
/plugin install ship@harness
```

Also installs: `core`.

## Skills

| Skill | Does |
|-------|------|
| `/ci-triage` | Classifies a red CI build as regression, flaky, or environment and returns a one-sentence root cause with the evidence and the next action |
| `/finish-branch` | Closes out a finished feature or fix branch — verifies it, then offers merge, open PR/MR, keep, or discard, and cleans up the worktree and local branch afterwards |
| `/release-checklist` | Walks a release through a fixed checklist — scope frozen, gates green, migrations safe, release notes drafted, tag, deploy, smoke check, rollback ready — and stops on the first unmet item |
| `/write-migration` | Writes or reviews a database/schema migration so it is reversible, non-locking and deployable while old code still runs — expand/contract, backfill separated, down path tested |

All plugins: [`../README.md`](../README.md).
