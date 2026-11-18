# guards

Opt-in guard-rail hooks for a stricter session: a commit gate on secrets and debug artifacts, a push gate that wants evidence, a scope flag on every prompt, a command log for the PR's Witness line, and a handoff written at the end of each session.

**For:** anyone who wants the rails tighter than the always-on core gates, on their own machine. Nothing here arrives with a plain role install: every hook that can block a commit beyond `core` and `dev` lives in this plugin, so it is a deliberate choice.

## Skills

| Skill      | Does                                                                                                        |
| ---------- | ----------------------------------------------------------------------------------------------------------- |
| `/worklog` | Shows the work log the sessions on one clone share, or records this session's task or a note for the others |

## Hooks

| Hook                  | Event                                 | Does                                                                                                                               |
| --------------------- | ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `session-resume`      | session start, resume, clear, compact | Injects the handoff from your state dir once, then deletes it, and points at the team, personal and global lesson indexes          |
| `scope-gate`          | every prompt                          | Flags implementation-intent prompts for the Auto-Coordinator: high-risk patterns, stale memory                                     |
| `commit-quality-gate` | before `git commit`                   | Blocks a commit with secrets, debug artifacts or failing tests                                                                     |
| `risk-corroboration`  | before `git commit`                   | Blocks a commit whose staged diff trips a hard-gate signal (auth, migration, security, provider, contract) above the declared lane |
| `push-evidence`       | before a push, PR or MR               | Asks the user when no test, lint or build ran after the last change                                                                |
| `blast-radius-check`  | after Edit, Write                     | Flags an edit to a file outside the active `PLAN.md` file set                                                                      |
| `format-on-edit`      | after Edit, Write                     | Formats the edited file with the project's own formatter                                                                           |
| `headroom-compress`   | after Bash                            | A soft hint to compress very large output when headroom is installed                                                               |
| `run-log`             | after Bash                            | Records each command to `.git/claude-run-log.jsonl`, so a PR's Witness line is filled from what ran, never typed                   |
| `session-handoff`     | on stop                               | Rewrites the handoff in your state dir after every reply: open specs, pending escalations, where the last reply stood              |
| `notify-on-finish`    | on stop                               | A macOS notification when Claude finishes a turn, so long runs need no watching                                                    |
| `worklog`             | start, prompt, Edit, Write, end       | Keeps the sessions' shared work log in `.git/claude-worklog/` and guards edits with it (below)                                     |

### `worklog`: parallel sessions on one clone

Every session logs its task, the files it edits and the export names it writes to `<git common dir>/claude-worklog/`, which all worktrees of the clone share and git never commits. Each session is told what the others are doing at its start and on each prompt.

| Situation                                                                    | The hook                                                                                                               |
| ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Another live session has uncommitted edits to the file, in the same checkout | Refuses the edit, names the holder and a pending path for the intended version; says on a later prompt when it is free |
| A session in another worktree edited the same path                           | Refuses once with that session's task and the command to see its change; the repeated call goes through                |
| A new file exports a name another live session already wrote                 | Refuses once and names the file that has it                                                                            |

A file is held while its last editor is live (a hook fired in the last 30 minutes) and git still shows the file as changed: a commit, a revert, the session ending or going silent frees it. Only Edit and Write are seen, not writes through the shell, and only sessions on this machine. Remove a clone's log with `rm -rf "$(git rev-parse --git-common-dir)/claude-worklog"`.

One more script lives in the folder but is not registered here: `agent-progress.sh` is copied into a project only by the standalone mode of `scripts/init.sh` (core).

## Depends on

`dev` (and through it `core`, `plan`, `review`, `progress`).

## Install

```text
/plugin install guards@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
