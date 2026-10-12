---
model: opus
effort: high
name: review-checklist
description: Reviews the current diff or a PR in a fixed order — correctness → tests → readability → security → scope — and returns at least three actionable comments plus a PR-description check. Use for self-review before opening a PR or for reviewing a teammate's PR. Does not replace the built-in /code-review or /code-review ultra.
when_to_use: before opening a PR, reviewing a teammate's PR, "review this", "check my diff", "could someone implement/review from this description"
---

# review-checklist — the Day-3 review, enforced

**Invoke:** `/review-checklist [PR number | branch]` — default: current branch vs its base.

Escalation path: this skill → built-in `/code-review` → `/code-review ultra` when the diff touches auth, data or migrations. Run `/security-review` too when step 4 finds anything.

## Step 1 — Get the diff and the description

```bash
git diff "$(git merge-base HEAD origin/HEAD)"...HEAD   # local branch
gh pr view <n> --json title,body && gh pr diff <n>      # GitHub PR
glab mr view <n> && glab mr diff <n>                    # GitLab MR
```

Read the ticket or PR description first — scope (step 5) is judged against it. Then read the code **around** each hunk, not just the diff: the added line is usually fine alone; the bug is in how it meets the lines the diff doesn't show.

## Step 2 — Walk the checklist in order

Do not skip ahead: a correctness bug outranks every readability note.

| # | Check | Ask |
|---|-------|-----|
| 1 | **Correctness** | Does it do what the ticket says? Wrong conditions, off-by-one, null paths, error paths, races. Shared code (`packages/*`, `libs/*`, shared hooks/components) → check its other call sites. |
| 2 | **Tests** | Is there a test that fails without this change? Happy + error path? Run them — don't trust they pass. |
| 3 | **Readability** | Would the next person understand it without the author? Misleading names, deep nesting, dead code, comments that restate code. Did it re-implement something the shared layer already provides? |
| 4 | **Security basics** | Unvalidated input at a boundary, secrets, injection, authz on mutating paths, logging PII. |
| 5 | **Scope** | Every changed line traces to the ticket? Unrelated refactors, drive-by fixes, missing pieces of the ask. |

## Step 3 — PR description check

Answer: *could someone review or reimplement this from the description alone?* It needs what / why / how tested (/ screenshots for UI). Name what is missing.

## Output

```markdown
## Review — <branch or PR>
Verdict: approve | request changes

### 1 Correctness
- `path/file.ts:42` — <issue>. **Fix:** <concrete change>
### 2 Tests
...
### 5 Scope
...
### Description
<self-contained? what's missing>
```

## Rules

- At least **3 actionable comments** — each names a file:line and a concrete fix. If the diff is genuinely clean, say so per section instead of inventing findings.
- "Actionable" means the author can act without asking you a question. "Consider improving this" is not actionable.
- Every correctness finding names the concrete input or state that makes it fail. If you can't, verify it (Grep/Read/run) or drop it — an unverified worry costs the author time to disprove.
- Verify by running (tests, the repro) where possible; mark unverified findings as such.
- No style nits unless they hide a bug — the formatter owns style.
