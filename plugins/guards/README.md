# guards

Personal guard-rail hooks: branch guard (no direct push to dev/stag/prod — override with `HARNESS_ENV_BRANCHES`), commit gate, scope gate, blast-radius and session handoff. Opt-in.

## Install

```
/plugin marketplace add thanghokdps/claude-root
/plugin install guards@harness
```

Also installs: `dev`.

## Hooks

| Event | Script |
|-------|--------|
| SessionStart (startup|resume|clear|compact) | `session-resume.sh` |
| UserPromptSubmit | `scope-gate.sh` |
| PreToolUse (Bash) | `commit-quality-gate.sh` |
| PreToolUse (Bash) | `branch-guard.sh` |
| PreToolUse (Bash) | `risk-corroboration.sh` |
| PostToolUse (Edit|Write) | `blast-radius-check.sh` |
| PostToolUse (Edit|Write) | `format-on-edit.sh` |
| PostToolUse (Bash) | `headroom-compress.sh` |
| Stop | `session-handoff.sh` |
| Stop | `state-breadcrumb.sh` |
| Stop | `notify-on-finish.sh` |

All plugins: [`../README.md`](../README.md).
