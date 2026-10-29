# core

Session and project basics every role uses: verify-done evidence gate, project-init bootstrap, docs-sync after each feature, compact/compound memory, sync-memory, btw — and the always-on `branch-guard` hook.

## Hook (always on)

`hooks/branch-guard.sh` runs before every Bash call. It blocks any direct push to an environment branch (`dev develop stag stage staging prod production`; override with `HARNESS_ENV_BRANCHES`, empty turns it off) and force, delete or mirror pushes to protected branches, and fails closed on shell state it cannot follow. Every role plugin depends on `core`, so every install gets it, in any repo, with no project config.

`hooks/secret-guard.sh` runs before Read, Grep, Glob, Edit, Write and Bash. Reading, printing, copying or editing a secret file (`.env*` but not its templates, keys, `.p8`, keystores, service-account JSON, SSH keys) is denied: Claude asks for the value instead. Patterns: `hooks/secret-paths.txt` plus the repo's `.claude/secret-paths.txt`; `CLAUDE_SECRET_GUARD=0` turns it off for a session.

`hooks/sensitive-path.sh` runs before Edit, Write and Bash. An edit to a secret, CI/deploy config or `.claude/settings*.json` asks the user first, unless the ticket's `plan.md` names the path. Patterns: `hooks/sensitive-paths.txt` and `hooks/secret-paths.txt`, plus the repo's `.claude/sensitive-paths.txt`; `CLAUDE_SENSITIVE_PATHS=0` turns it off.

`hooks/step-limit.sh` runs before every tool call. A subagent past `CLAUDE_STEP_LIMIT` (90) tool calls is stopped and must reply with what is done, what is stuck and the last error, so the main session can re-plan. The main session is not counted unless `CLAUDE_STEP_LIMIT_MAIN=1`. It costs no tokens.

`hooks/compact-advisor.sh` runs on Stop. Past `CLAUDE_COMPACT_ADVISE_TOKENS` (200k) of context it shows the user one line suggesting `/compact`, again every 100k more. The model never sees it, so it costs nothing.

`hooks/repo-profile.sh` runs on SessionStart, and on SubagentStart so subagents get the same profile (they never write settings). From the manifests and marker folders alone (no model call) it tells the session what the repo is — stack, AI assistant, DB tool, whether `.claude/docs/` exists — and which kit skills to prefer, in 3–4 lines. In an AI-assistant repo it enables `agent@harness` in `.claude/settings.local.json` (excluded from git, effective next session) unless the project or local settings say `false`. `CLAUDE_REPO_PROFILE=0` turns it off.

## Install

```
/plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git
/plugin install core@harness
```

GitLab needs the VPN and an SSH key. Outside it, add the GitHub mirror instead: `/plugin marketplace add thanghokdps/claude-root`.

Also installs: `progress`.

## Skills

| Skill | Does |
|-------|------|
| `/btw` | Answer a quick question or do a quick lookup without interrupting the current task or losing context |
| `/compact` | Compact the current conversation — summarize what's been done, merge into persistent memory and HANDOFF.md, so the next session resumes with full context |
| `/compound` | Crystallize learnings from the current session into persistent docs/solutions/ files |
| `/docs-sync` | Brings .claude/docs/ and CLAUDE.md up to date with a branch's diff — maps each change to the doc it makes stale, edits only those sections, and commits them with the code |
| `/project-init` | One-time project scan that bootstraps the full .claude/ workspace — docs, agents, hooks, rules, skills, templates, memory, and CLAUDE.md — all tailored to this specific project; TypeScript repos also get the anti-slop Oxlint rules vendored at a pinned SHA; a repo with a GitHub/GitLab remote is offered server rules that block direct pushes to the default branch and dev/stag/prod |
| `/sync-memory` | Pulls the latest commits and rebuilds memory from your own, updating .claude/memory/commits/ and last-sync.txt |
| `/verify-done` | Evidence gate before claiming work is finished — re-runs the checks that prove the task's "done when" condition, in this session, and reports output instead of assurances |

## Base rules (installed to `~/.claude/rules/`, each loads only for matching files)

| Rule | Covers |
|------|--------|
| `app-structure.md` | Fullstack folder ownership, size and naming |
| `api-contract.md` | Endpoint order, error codes, 404 for another user's resource, additive contracts, route test matrix |
| `data-access.md` | Owner-scoped repositories, parameterised queries, no N+1, transactions, migrations, real-engine tests |

Also: `git.md`, `security.md`, `code-quality.md`, `testing.md`, `typescript.md`.

All plugins: [`../README.md`](../README.md).
