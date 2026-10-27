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

### No remote yet, or an empty one

A new repo has no `origin` or an `origin` with no branches (`git ls-remote origin` prints nothing). Then:

1. Add the remote in the URL form this machine already uses: an SSH host alias from `~/.ssh/config` (`Host github-<user>`) or the form of another repo's `origin` (`git -C <other-repo> remote get-url origin`). Use HTTPS only if no SSH form is set up — an HTTPS remote asks for a username and password the SSH key does not answer.
2. The first `main` is the user's push: give them `git push -u origin main` to run. Claude does not push to `main`, even into an empty repo.
3. Then continue from a feature branch as usual.

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
