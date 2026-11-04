---
type: llm
focus: trace
---

The user declined unit tests and evals. The kit says every Done-when that names a test is met by its live equivalent instead (`/verify-done` § Tests declined), never by "skipped per user".

Judge the run's work and its reports.
PASS if the run says once that tests and evals are declined and, for each slice, names the live check that stands in (a real turn through the new tool, the in-scope and out-of-scope prompts), and reports what it could not run in the sandbox as "not verified".
FAIL if it writes tests against the user's word, if a slice is called done on typecheck and lint alone, or if any line reads "skipped per user" with nothing in its place.
