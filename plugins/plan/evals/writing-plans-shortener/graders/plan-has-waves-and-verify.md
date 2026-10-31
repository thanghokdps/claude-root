---
type: llm
focus: trace
---

Judge the `specs/shortener/PLAN.md` the run wrote or attempted. An Edit or Write tool input counts even when the sandbox denied it.

The design names three files (`src/codes.py`, `src/store.py`, `src/handler.py`), tests with `unittest`, and no dependencies.

PASS if PLAN.md exists (written or attempted) with a file map of exact paths (no globs) including the matching test files, tasks each assigned to a wave, a `verify` shell command per task that can exit 0 (for example `python3 -m unittest tests.test_codes`), test-first ordering inside a task or pair of tasks, and no two tasks in the same wave touching the same file.
FAIL if no PLAN.md is written or proposed, tasks lack a verify command, files appear as globs or "somewhere in src", waves are missing, or implementation code is written to src/ instead of a plan.
