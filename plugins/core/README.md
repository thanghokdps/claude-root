# core

Session and project basics every role uses: verify-done evidence gate, project-init bootstrap, compact/compound memory, sync-memory, btw — and the always-on `branch-guard` hook.

## Hook (always on)

`hooks/branch-guard.sh` runs before every Bash call. It blocks any direct push to an environment branch (`dev develop stag stage staging prod production`; override with `HARNESS_ENV_BRANCHES`, empty turns it off) and force, delete or mirror pushes to protected branches, and fails closed on shell state it cannot follow. Every role plugin depends on `core`, so every install gets it, in any repo, with no project config.

## Install

```
/plugin marketplace add thanghokdps/claude-root
/plugin install core@harness
```

Also installs: `progress`.

## Skills

| Skill | Does |
|-------|------|
| `/btw` | Answer a quick question or do a quick lookup without interrupting the current task or losing context |
| `/compact` | Compact the current conversation — summarize what's been done, merge into persistent memory and HANDOFF.md, so the next session resumes with full context |
| `/compound` | Crystallize learnings from the current session into persistent docs/solutions/ files |
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
