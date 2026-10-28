# guards

Personal guard-rail hooks: commit gate, scope gate, blast-radius and session handoff. Opt-in.

## Install

```
/plugin marketplace add thanghokdps/claude-root     # GitHub (public, no VPN)
# or: /plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git   # GitLab (team: VPN + SSH key)
/plugin install guards@harness
```

Also installs: `dev`.

## Hooks

| Event | Script |
|-------|--------|
| SessionStart (startup|resume|clear|compact) | `session-resume.sh` |
| UserPromptSubmit | `scope-gate.sh` |
| PreToolUse (Bash) | `commit-quality-gate.sh` |
| PreToolUse (Bash) | `risk-corroboration.sh` |
| PreToolUse (Bash) | `push-evidence.sh` — before `git push` / PR / MR, asks when no test, lint or build ran after the last change |
| PostToolUse (Edit|Write) | `blast-radius-check.sh` |
| PostToolUse (Edit|Write) | `format-on-edit.sh` |
| PostToolUse (Bash) | `headroom-compress.sh` |
| PostToolUse (Bash) | `run-log.sh` — logs each command to `.git/claude-run-log.jsonl` for the PR's Witness line |
| Stop | `session-handoff.sh` |
| Stop | `state-breadcrumb.sh` |
| Stop | `notify-on-finish.sh` |

All plugins: [`../README.md`](../README.md).
