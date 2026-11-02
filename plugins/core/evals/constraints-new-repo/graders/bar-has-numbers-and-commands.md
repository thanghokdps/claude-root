---
type: llm
focus:
  source: file
  path: CONSTRAINTS.md
---

This is `CONSTRAINTS.md` at the repo root after the run (empty when the run wrote it elsewhere or not at all).

The repo has scripts `npm run lint` and `npm test` (node --test), eslint, and no coverage tool or vulnerability scanner configured beyond `npm audit`.

PASS if the file is non-empty and has a table of enforced rows each with a numeric threshold (for example 0 lint errors, changed-line coverage at or above some percent, no high vulnerabilities) AND the command that produces the verdict (such as `npm run lint`, `npm test`, `npm audit --audit-level high`), and any dimension without a command or tool in the repo sits in a measured-only section instead.
FAIL if the file is missing or elsewhere, a threshold is stated without a command, an enforced row names a tool the repo does not have as if it ran today, or the bar is only "tests pass".
