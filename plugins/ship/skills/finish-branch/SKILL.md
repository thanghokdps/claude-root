---
model: opus
effort: medium
name: finish-branch
description: Closes out a finished feature or fix branch — verifies it, then offers merge, open PR/MR, keep, or discard, and cleans up the worktree and local branch afterwards. Use when the implementation tasks are complete and the work needs to land or be parked.
when_to_use: all tasks in the plan are done, "wrap this up", "ship this branch", "open the MR", "clean up the worktree", finishing work in a git worktree
---

# finish-branch — land it or park it, cleanly

**Invoke:** `/finish-branch`

## Step 1 — Verify first

Run `/verify-done`. If anything fails, stop here and report — a branch is not finished while its proof fails.

## Step 2 — Show the state

```bash
git status -sb
git log --oneline "$(git merge-base HEAD origin/HEAD)"..HEAD
git diff --stat "$(git merge-base HEAD origin/HEAD)"...HEAD
```

Flag uncommitted changes, fixup commits worth squashing, and commits that break the one-logical-change rule.

Before offering a PR, check what would make it fail or land unchecked, and report each hit:

- **No remote** → add one in the form this machine already pushes with: an SSH host alias from `~/.ssh/config` or another repo's `git remote get-url origin` (`git@github-<alias>:owner/repo.git`). HTTPS only when nothing uses SSH; an HTTPS remote on an SSH machine prompts for a password.
- **Empty remote** (`git ls-remote` shows no base branch) → the first push of `main` is the user's: print `git push -u origin main` for them; the PR follows once it exists.
- **CI secrets** → the `secrets.<NAME>` the workflows read (`grep -rhoE 'secrets\.[A-Z0-9_]+' .github/workflows`) minus `gh secret list` (names only). A missing one is named with the job it breaks, before the PR goes red on it; never read or set a value.
- **Unprotected base** → `gh api repos/<owner>/<repo>/branches/<base>/protection` returning 404 means no required checks, so a red PR can be merged. Say so and point to the rulesets `/project-init` (core) offers.

## Step 3 — Ask which way (one question)

Ask through `AskUserQuestion` with these four options, the one that fits the branch first with `(Recommended)`:

| Option | What happens |
|--------|--------------|
| **Open PR/MR** | If the `developers` plugin is enabled, hand off to `developers:create-mr` (it follows the project's commit/remote/base-branch conventions). Otherwise push, draft what / why / how tested, open via `gh pr create` or `glab mr create` |
| **Merge locally** | Only if the user explicitly wants it and the base is not a protected branch |
| **Keep** | Leave branch and worktree as they are; note the state in `specs/HANDOFF.md` |
| **Discard** | Show exactly what will be lost, get an explicit yes, then delete |

## Step 4 — Clean up (after the chosen action succeeds)

- Worktree: `git worktree list`, then `git worktree remove <path>` for this branch's worktree.
- Local branch: delete only after it is merged or the user chose discard.
- Never force-push, delete a remote branch, or merge into `main`/`master` without explicit confirmation.

## Output

The chosen action, the PR/MR link or merge commit, and what was cleaned up.
