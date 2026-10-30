# guards

Opt-in guard-rail hooks for a stricter session: a commit gate on secrets and debug artifacts, a push gate that wants evidence, a scope flag on every prompt, a command log for the PR's Witness line, and a handoff written at the end of each session.

**For:** anyone who wants the rails tighter than the always-on core gates, on their own machine. Nothing here arrives with a plain role install: every hook that can block a commit beyond `core` and `dev` lives in this plugin, so it is a deliberate choice.

## Skills

None. This plugin is hooks only.

## Hooks

| Hook | Event | Does |
|---|---|---|
| `session-resume` | session start, resume, clear, compact | Injects `specs/HANDOFF.md` (written by `session-handoff`) so a new session continues where the last one stopped |
| `scope-gate` | every prompt | Flags implementation-intent prompts for the Auto-Coordinator: high-risk patterns, stale memory |
| `commit-quality-gate` | before `git commit` | Blocks a commit with secrets, debug artifacts or failing tests |
| `risk-corroboration` | before `git commit` | Blocks a commit whose staged diff trips a hard-gate signal (auth, migration, security, provider, contract) above the declared lane |
| `push-evidence` | before a push, PR or MR | Asks the user when no test, lint or build ran after the last change |
| `blast-radius-check` | after Edit, Write | Flags an edit to a file outside the active `PLAN.md` file set |
| `format-on-edit` | after Edit, Write | Formats the edited file with the project's own formatter |
| `headroom-compress` | after Bash | A soft hint to compress very large output when headroom is installed |
| `run-log` | after Bash | Records each command to `.git/claude-run-log.jsonl`, so a PR's Witness line is filled from what ran, never typed |
| `session-handoff` | on stop | Writes a comprehensive `specs/HANDOFF.md` at session end |
| `state-breadcrumb` | on stop | Appends a session breadcrumb to memory |
| `notify-on-finish` | on stop | A macOS notification when Claude finishes a turn, so long runs need no watching |

Two more scripts live in the folder but are not registered here: `save-commit-memory.sh` and `agent-progress.sh` are copied into a project only by the standalone mode of `scripts/init.sh` (core).

## Depends on

`dev` (and through it `core`, `plan`, `review`, `progress`).

## Install

```text
/plugin install guards@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
