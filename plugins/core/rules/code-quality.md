# Code quality

- Optimize for the reader: names say what, not how; one job per function (~30 lines); nesting >3 → guard clauses.
- DRY at three copies, not two. Delete dead code and unused imports — git remembers.
- No N+1 queries or I/O inside loops; profile before optimizing.
- Take the first option that fully works: skip it if nobody asked → reuse what the codebase has → stdlib or platform → an installed dependency → one readable line → the minimum new code. Never add a dependency for a few lines.
- Be lean in the solution, never in its reach: update every caller, test and fixture the change breaks.

## Shortcuts
- A deliberate shortcut with a known limit gets one comment: `shortcut: <the limit>, <when to upgrade>` (e.g. `// shortcut: in-memory, fine for one process; move to Redis when we scale out`). `/debt-ledger` lists them.
- A marked shortcut is a decision, not a review finding, unless the expected load already crosses its limit. An unmarked one is a finding.
- Never take a shortcut on validation at trust boundaries, error handling that prevents data loss, security or accessibility.

## Comments
- Explain WHY, never WHAT. Default 1 line; exported symbol with a real constraint 2–3; subtle invariant ≤6; more than that belongs in docs.
- Say it once per file; don't restate the line below or the identifier.
- Keep the facts (numbers, error codes, ticket refs, why the obvious approach was rejected); cut the narrative.
- When shortening a comment, re-check the claim — negations and comparisons invert easily.
- Change files with the Edit and Write tools, never with shell heredocs, `sed -i` or a script, so the edit hooks (lint, format) run on every change. Shell writes are for generated files and scratch output. The `edit-guard` hook (core) blocks `sed -i`, `perl -i`, redirects, `tee` and inline scripts that write a tracked repo path; write scratch output outside the repo or to a gitignored path, and keep a generator in a script file.
