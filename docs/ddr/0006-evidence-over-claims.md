# 0006 — Evidence over claims: run logs, citations, before and after

**Status:** Accepted (28 Oct 2026)

## Context

"Tests pass" and "works now" in a PR are the model's words. A reviewer cannot tell a check that ran from one that was described, and a question answered from memory is a guess.

## Decision

- `run-log.sh` (guards) records every shell command in `.git/claude-run-log.jsonl`. `/create-pr` fills the **Witness** line from it with `witness.sh`; the line is never typed by hand, and "not recorded" stays when there is no log.
- A PR's **Demonstration** shows Before and After produced the same way (command output or screenshot), and a one-line Delta.
- `/resolve-question` answers a fact only with a `file:line` citation opened in the session; only a real choice goes to the user.
- `push-evidence.sh` asks before a push when no check ran after the last change.

## Consequences

- A reviewer reads what ran, with times, next to the diff.
- Fewer questions reach the user, and none that the repo already answers.

## Where

`plugins/guards/hooks/run-log.sh`, `push-evidence.sh`, `plugins/review/skills/create-pr/`, `plugins/dev/skills/resolve-question/`.
