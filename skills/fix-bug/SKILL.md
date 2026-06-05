# fix-bug — Find root cause → minimal fix → verify → commit

**Invoke:** `/fix-bug <symptom or description>`

**Rule:** Fix ONLY the specific bug. No refactoring, no cleanup, no "while I'm here" changes.

---

## Stage 1 — Reproduce

Before touching code, confirm the bug is real and reproducible:
```bash
# Run the failing test / command / scenario
# Document: exact input, expected output, actual output
```

If the bug cannot be reproduced → report to user, ask for more context.

## Stage 2 — Root cause

Trace the failure to its origin — not just where it crashes, but WHY.

Tools to use:
- `grep -r "<error message>" src/` — find where the error is thrown
- `git log --oneline src/<file>` — was this recently changed?
- `git log --all --grep="<keyword>" --oneline` — is there a relevant commit message?
- Read the affected file(s) — understand the data flow

Do NOT guess. If root cause is unclear after reading 3 files → report findings to user.

## Stage 3 — Minimal fix

Write the smallest possible fix that addresses the root cause.

Rules:
- Change as few lines as possible
- Do NOT refactor surrounding code
- Do NOT rename variables "while you're there"
- Do NOT add error handling for cases that can't happen
- If fix requires a larger structural change → stop, report to user, propose the fix as a separate `/feature`

## Stage 4 — Verify

```bash
# Run the specific test(s) that cover the bug
# Re-run the failing scenario from Stage 1
# Run the broader test suite if available
```

TypeScript projects: `npx tsc --noEmit` — zero new errors allowed.

If verification reveals a different root cause → go back to Stage 2.

## Stage 5 — Commit

```bash
git add <only the files needed for the fix>
git commit -m "fix: <what was wrong and what fixed it>"
```

Commit message should describe the fix, not the symptom:
- Good: `fix: prevent double-emit of TOOL_CALL_END when parallel tool calls overlap`
- Bad: `fix: bug in tool call handling`

---

## Memory: save if non-obvious

After committing, if the root cause was subtle or non-obvious, write a feedback memory:
```
File: .claude/memory/feedback/YYYY-MM-DD.md
Content: what the bug was, why it was non-obvious, pattern to watch for
```

This prevents the same class of bug from being introduced again.
