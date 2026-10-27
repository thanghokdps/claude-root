# Code quality

- Optimize for the reader: names say what, not how; one job per function (~30 lines); nesting >3 → guard clauses.
- DRY at three copies, not two. Delete dead code and unused imports — git remembers.
- No N+1 queries or I/O inside loops; profile before optimizing.

## Comments
- Explain WHY, never WHAT. Default 1 line; exported symbol with a real constraint 2–3; subtle invariant ≤6; more than that belongs in docs.
- Say it once per file; don't restate the line below or the identifier.
- Keep the facts (numbers, error codes, ticket refs, why the obvious approach was rejected); cut the narrative.
- When shortening a comment, re-check the claim — negations and comparisons invert easily.
- Change files with the Edit and Write tools, never with shell heredocs, `sed -i` or a script, so the edit hooks (lint, format) run on every change. Shell writes are for generated files and scratch output. The `edit-guard` hook (core) blocks `sed -i`, `perl -i`, redirects, `tee` and inline scripts that write a tracked repo path; write scratch output outside the repo or to a gitignored path, and keep a generator in a script file.
