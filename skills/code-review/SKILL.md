---
model: opus
effort: high
name: code-review
description: Reviews the current diff for correctness bugs, security issues, and cleanups, reporting findings ranked by severity. Use when the user asks for a review of uncommitted or branch changes.
when_to_use: after implementing a change, before opening a PR, or when the user says review this diff
---

# code-review — Review diff for correctness bugs and cleanups

**Invoke:** `/code-review [low|medium|high]`

Default effort: `medium`.

---

## Stage 1 — Get the diff

```bash
git diff main...HEAD          # all commits on this branch
# OR
git diff HEAD~1..HEAD         # last commit only
```

## Stage 2 — Review by effort level

### low (quick, high-confidence only)
Focus only on:
- Obvious correctness bugs (null deref, off-by-one, wrong condition)
- Hardcoded secrets or credentials
- Missing input validation at system boundaries (user input, external APIs)

Return: max 5 findings.

### medium (default)
Everything in `low`, plus:
- Logic errors in complex conditions
- Missing error handling at system boundaries (not internal code)
- Duplicate code that could reuse an existing function (only if the reuse is obvious)
- Type errors or unsafe casts
- Security issues: SQL injection, XSS, command injection (OWASP top 10)

Return: max 10 findings.

### high
Everything in `medium`, plus:
- Performance issues visible from the diff (N+1 queries, unnecessary re-renders)
- Naming that actively misleads (not style — correctness of intent)
- Missing tests for non-trivial new logic
- Architectural concerns: new abstraction vs reuse, module boundary violations

Return: all findings, grouped by severity.

---

## Severity labels

- `🔴 MUST FIX` — correctness bug or security issue
- `🟡 SHOULD FIX` — likely problem, but not definitely broken
- `🔵 CONSIDER` — improvement, not a bug

---

## Format

```markdown
### 🔴 MUST FIX — <short label>
**File:** `src/path/to/file.ts:42`
**Issue:** <what's wrong>
**Fix:** <minimal fix>

---
### 🟡 SHOULD FIX — <short label>
...
```

---

## Rules

- Only report what you can justify from the diff — no speculation
- Do NOT suggest refactoring unrelated to correctness or security
- Do NOT comment on style, naming, or formatting unless it causes bugs
- If you're uncertain about a finding → label it `🔵 CONSIDER` with the uncertainty stated
