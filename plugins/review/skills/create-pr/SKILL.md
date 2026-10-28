---
effort: high
name: create-pr
description: Generates a structured PR description from the current branch diff. Fills a PR_TEMPLATE.md with title, summary (why not how), tasks completed, file changes table, and notes. Does NOT push or create the PR — outputs the template for review.
when_to_use: drafting only the PR/MR description text, "describe this branch"; to commit, push and open the MR use developers:create-mr when available
---

# Create PR

Generate a reviewer-friendly PR description from the current branch's changes.

---

## Process

### Step 1 — Gather context

Base branch, commits and file stats, collected when this skill loads (base = the remote's default branch, not always `main`):

```!
git rev-parse --abbrev-ref origin/HEAD 2>/dev/null || echo "origin/HEAD not set: base is main"
git log --oneline origin/HEAD..HEAD 2>/dev/null | head -50
git diff --stat origin/HEAD...HEAD 2>/dev/null | tail -40
```

Read-only git only, no variables or `$(…)`: anything the CLI cannot permission-check (variables, `git symbolic-ref`, extra flags such as `rev-parse --verify`) silently drops the whole skill. Then read the full diff for analysis: `git diff origin/HEAD...HEAD` (or `main...HEAD` when origin/HEAD is not set).

Also read `specs/<slug>/SUMMARY.md` if it exists — use "What changed" and "Rationale" sections.

Then run `bash ${CLAUDE_SKILL_DIR}/scripts/witness.sh`: the test, lint, build and eval commands this branch really ran, read from the run log that the run-log hook (guards, if installed) writes. Paste its output as is into **Witness**.

### Step 2 — Analyze changes

Group changes by:
- **Type**: feat | fix | refactor | test | docs | chore
- **Module**: which layer or feature area was touched
- **Impact**: what user-visible or system-visible behavior changed

### Step 3 — Draft the PR description

**Title format**: `<type>(<scope>): <short description>` — max 72 characters.

Examples:
- `feat(auth): add JWT refresh token rotation`
- `fix(upload): handle files larger than 10MB`
- `refactor(user-service): extract repository pattern`

**Body format**:

```markdown
## Summary

<1–3 sentences on WHY this change exists — the problem it solves, not what it does>

## Tasks completed

- <bullet: what was done, one line each>
- <bullet>

## File changes

| File | Action | Notes |
|------|--------|-------|
| path/to/file.py | modified | <brief note> |
| path/to/new.py | added | |

## Demonstration

- **Before:** <what a user or caller saw before: the error, the output, the missing screen; a command and its output, or a screenshot>
- **After:** <the same thing now, produced the same way>
- **Delta:** <one line: what changed for the user>
- **Witness:** <the witness script's output, unedited>

## Test coverage

<How was this tested? What commands verify it?>

## Notes

<Optional: breaking changes, migration steps, follow-ups, caveats>
```

### Step 4 — Write to PR_TEMPLATE.md

Save the filled template to `PR_TEMPLATE.md` in the repo root.

### Step 5 — Show the user

Display the template and say:
"Review this PR description. To create the PR, run:
`gh pr create --title '<title>' --body-file PR_TEMPLATE.md`"

---

## Rules

- **Why, not how** — the summary explains the problem solved, not the implementation
- No line-by-line code explanations in the body
- Title must be ≤ 72 characters
- If SUMMARY.md exists in specs/, use its Rationale as the PR summary
- **Demonstration is shown, not claimed** — Before and After are outputs or screenshots taken the same way, never "works now". A change with no visible behaviour (refactor, docs) says so in Delta and points at the unchanged test run.
- Never type or edit the Witness line: when the script says "not recorded", keep that line and name the commands to run in Test coverage
- Do NOT push or create the PR — output only
