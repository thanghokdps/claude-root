---
type: llm
focus: trace
---

The repo requires an `eval/triggers/<name>.json` for every skill: 3 positive prompts that must rank the skill top-3 and 1 negative owned by a neighbour skill (see `eval/triggers/greet.json`). An Edit or Write tool input counts even when the sandbox denied it.

PASS if the run writes or attempts `eval/triggers/changelog-summary.json` with `"skill": "changelog-summary"`, three positive prompts about summarizing commits into a changelog, and at least one negative with an owner; and it adds a `changelog-summary` entry to the demo row of `plugins/README.md`.
FAIL if no trigger case is written or attempted, it has fewer than three positives or no negative, or the skill is not listed in `plugins/README.md`.
