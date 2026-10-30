# core

Session and project basics every role uses: the evidence gate before "done", the project bootstrap, docs and memory that survive the session, and the always-on safety hooks.

**For:** everyone. Every role plugin depends on `core`, so every install gets it, in any repo, with no project config.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/verify-done` | You are about to say done, fixed, passing or ready, or before a commit, PR or handoff. Re-runs the checks that prove the "done when" condition and reports output, not assurances | "ready for review" (fires on its own) |
| `/project-init` | Once per existing repo, and again after a big architecture change. Scans the code and writes `.claude/` (docs, rules, memory) and a project `CLAUDE.md` with real paths and commands | `/project-init` |
| `/docs-sync` | A feature, scaffold or fix is about to land. Maps the branch's diff to the project docs it makes stale and edits only those sections | "update the docs before the PR" |
| `/compact` | The conversation is getting long, or you are ending the session. Writes `specs/HANDOFF.md` and merges learnings into memory so the next session resumes | `/compact` |
| `/compound` | A session found a hard bug, a mistake or a pattern worth keeping. Writes it to `docs/solutions/` | `/compound` |
| `/sync-memory` | Starting a session on a shared repo, or after a teammate pushed. Pulls and rebuilds memory from your own commits | `/sync-memory` |
| `/btw` | A quick question mid-task, with no tasks, specs or side effects | `/btw which file handles auth?` |

## Hooks (always on)

| Hook | Event | Does |
|---|---|---|
| `branch-guard` | before Bash | Blocks a direct push to `main` or an environment branch (`dev develop stag stage staging prod production`) and force, delete or mirror pushes to protected branches. `HARNESS_ENV_BRANCHES` overrides the list |
| `secret-guard` | before Read, Grep, Glob, Edit, Write, Bash | A secret file (`.env*` but not its templates, keys, keystores, service-account JSON, SSH keys) is never read, printed, copied or edited; Claude asks for the value. Patterns: `hooks/secret-paths.txt` plus the repo's `.claude/secret-paths.txt`. `CLAUDE_SECRET_GUARD=0` turns it off for a session |
| `sensitive-path` | before Edit, Write, Bash | An edit to secrets, CI/deploy config or `.claude/settings*.json` asks the user first, unless the ticket's `plan.md` names the path. `CLAUDE_SENSITIVE_PATHS=0` turns it off |
| `edit-guard` | before Bash | Repo files change through Edit/Write, never `sed -i`, heredocs or redirects, so the per-edit lint and format hooks run on every change. Scratch output outside the repo is fine |
| `step-limit` | before every tool | A subagent past `CLAUDE_STEP_LIMIT` (90) tool calls stops and reports what is done, what is stuck and the last error, so the main session can re-plan |
| `repo-profile` | session and subagent start | From manifests and marker folders alone (no model call) tells the session what the repo is (stack, AI assistant, DB tool, docs present) and which skills to prefer. It enables the role packs the stack needs (`frontend@harness`, `backend@harness`, `ai@harness`) and, in a workplace repo, `workplace@harness`, in `.claude/settings.local.json`. `CLAUDE_REPO_PROFILE=0` turns it off |
| `compact-advisor` | on stop | Past `CLAUDE_COMPACT_ADVISE_TOKENS` (200k) of context, shows the user one line suggesting `/compact`. The model never sees it |
| `learn-capture` + `learn-promote` | every 50 tool calls; session start | Lessons capture themselves: a background Haiku reflector proposes them from a scrubbed digest of the session; at the next session start the valid ones land in `.claude/docs/solutions/` with an index line, stale ones retire, and one seen in two or more repos is copied to `~/.claude/docs/solutions/` |

## Also in this plugin

- **Rules** installed to `~/.claude/rules/` by `scripts/install.sh`: `git`, `security`, `code-quality`, `model-cost` (always on); `typescript`, `testing`, `app-structure`, `api-contract`, `data-access` (only for matching files).
- **Templates and stacks** that `/project-init` and `scripts/init.sh` copy into a project: `CLAUDE.md`, `settings.json`, spec templates, project agents and commands, and the `react-native` stack bundle (framework rules live in the role packs).

## Depends on

`progress`.

## Install

```text
/plugin install core@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
