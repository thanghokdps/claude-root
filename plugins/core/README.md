# core

Session and project basics every role uses: verify-done evidence gate, project-init bootstrap, compact/compound memory, sync-memory, btw.

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
| `/project-init` | One-time project scan that bootstraps the full .claude/ workspace — docs, agents, hooks, rules, skills, templates, memory, and CLAUDE.md — all tailored to this specific project |
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
