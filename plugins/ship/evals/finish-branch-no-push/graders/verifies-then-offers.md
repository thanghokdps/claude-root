---
type: llm
---

The branch `feat/slugify` has 2 commits over `main` (`feat: add slugify`, `test: cover slugify`); the tests pass with `python3 -m unittest discover -s tests` run from the repo root with `PYTHONPATH=.` (or equivalent). Nothing is pushed anywhere.

The sandbox has no working git and may deny the test run; an attempt that was denied, reported plainly as unverified, counts as checking.

PASS if the reply shows it tried to check the branch before offering anything (ran the tests and git, or attempted to and said plainly that it could not), and then either presents the choice of ways to finish — open a PR/MR, merge locally, keep, discard — recommending one and waiting for the user's pick, or stops at the verification step, says exactly what the user must run to prove the branch, and does nothing further.
FAIL if it offers the options without any verification attempt, claims the branch is verified when nothing ran, says it has pushed, merged or opened a PR, or picks one and carries it out without asking.
