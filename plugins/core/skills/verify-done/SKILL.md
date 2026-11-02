---
effort: medium
name: verify-done
description: Evidence gate before claiming work is finished — re-runs the checks that prove the task's "done when" condition, in this session, and reports output instead of assurances. Use whenever you are about to say done, fixed, passing, ready, or shipped, or before handing off, committing, or opening a PR.
when_to_use: about to say "done", "fixed", "all tests pass", "ready for review", before a commit, PR, or handoff, after a subagent reports success
---

# verify-done — no "done" without fresh evidence

**Invoke:** `/verify-done` (or automatically, right before declaring completion)

## Step 1 — Restate the finish line

Write the task's success criterion in one line: `Done when <observable check>`. If none was agreed, derive it from the request and say so.

## Step 2 — Run the proof now

Run every command that proves it in **this** session — results from earlier turns or from a subagent's summary do not count.

| Claim | Proof |
|-------|-------|
| Bug fixed | The reproduction (test or repro steps) now passes, and it failed before the fix |
| Feature works | Its test passes **and** the running app/endpoint shows the behaviour (browser, simulator, curl) |
| Tests pass | Full relevant suite output, with counts — not a single file |
| Types/lint clean | Project typecheck and lint commands exit 0 |
| Refactor safe | Same suite green before and after; no behaviour change in the diff |
| Quality bar held | `CONSTRAINTS.md` exists at the repo root (`/constraints`): every row of **Enforced with numbers** whose `Runs at` is `every edit` or `task end` is run by its `Checked by` command and reported with its number; a **Measured** metric that moved in the wrong direction is a finding |

## Step 3 — Check what was not asked for

`git diff --stat` — every file traces to the request; no debug output, commented-out code, or stray files.

## Output

```
Done when: <criterion>
Evidence:
- <command> → <exit code / key output line>
Not verified: <anything you could not run, and why>
Verdict: done | not done (<what is missing>)
```

## Rules

- A check you could not run is reported as "not verified", never as passing.
- "Should work", "looks correct", "probably" are not evidence.
- If the proof fails, the task is not done — go back to fixing, don't soften the report.
