# 0007 — Every skill's routing is tested for free; behaviour evals are paid and run before releases

**Status:** Accepted

## Context

A skill that never fires is dead weight, and one that fires on its neighbour's prompt does the wrong work. Running a real model on every change costs money on every PR.

## Decision

- Every skill has `eval/triggers/<name>.json`: three prompts that must rank it in the top 3, and one or two that belong to a neighbour. `scripts/check.sh` runs them on every change, with no model call.
- Behaviour evals with a real model (`scripts/eval-plugin.sh <plugin>`) are paid and run before a release or a demo, not on every PR.

## Consequences

- A new skill cannot merge without its routing cases; a collision between two skills fails the check.
- What a skill does once it fires is proven by the paid run and by real tickets, not by `check.sh`.

## Where

`eval/triggers/`, `scripts/eval-triggers.py`, `scripts/check.sh`, `scripts/eval-plugin.sh`.
