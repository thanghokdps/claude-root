---
type: llm
focus:
  source: file
  path: specs/shortener/PLAN.md
---

This is `specs/shortener/PLAN.md` after the run. The skill asks for complete code inside tasks, so code in the plan is expected; `no-implementation.md` checks for writes to `src/`. A verification-only task with no files of its own is fine.

The design names three files (`src/codes.py`, `src/store.py`, `src/handler.py`), tests with `unittest`, and no dependencies.

PASS if PLAN.md has a file map of exact paths (no globs) including the matching test files, tasks each assigned to a wave, a `verify` shell command per task that can exit 0 (for example `python3 -m unittest tests.test_codes`), test-first ordering inside a task or pair of tasks, and no two tasks in the same wave touching the same file.
FAIL if the file is missing, tasks lack a verify command, files appear as globs or "somewhere in src", or waves are missing.
