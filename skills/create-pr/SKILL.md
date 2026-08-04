---
model: opus
effort: high
name: create-pr
description: Generates a structured PR description from the current branch diff. Fills a PR_TEMPLATE.md with title, summary (why not how), tasks completed, file changes table, and notes. Does NOT push or create the PR — outputs the template for review.
---

# Create PR

Generate a reviewer-friendly PR description from the current branch's changes.

---

## Process

### Step 1 — Gather context

Run these commands:

```bash
git log main..HEAD --oneline          # commits on this branch
git diff main...HEAD --stat           # files changed + line counts
git diff main...HEAD                  # full diff for analysis
```

Also read `specs/<slug>/SUMMARY.md` if it exists — use "What changed" and "Rationale" sections.

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
- Do NOT push or create the PR — output only
