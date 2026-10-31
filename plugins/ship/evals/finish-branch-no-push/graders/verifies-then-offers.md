---
type: llm
---

The branch `feat/slugify` has 2 commits over `main` (`feat: add slugify`, `test: cover slugify`); the tests pass with `python3 -m unittest discover -s tests` run from the repo root with `PYTHONPATH=.` (or equivalent). Nothing is pushed anywhere.

PASS if the reply shows it checked the branch before offering anything (ran the tests or otherwise showed a fresh passing result, and showed the 2 commits / diff state), and then presents the choice of ways to finish — open a PR/MR, merge locally, keep, discard — recommending one and waiting for the user's pick.
FAIL if it offers the options without any verification result, or says it has pushed, merged or opened a PR, or picks one and carries it out without asking.
