---
model: opus
effort: medium
name: sync-remote
description: Keeps a repo's GitHub and GitLab remotes in sync, across one repo or many — fetches both, classifies every branch and tag (same, ahead, only on one side, diverged, conflicting tag), pushes the fast-forwards and missing tags after one confirmation, and leaves main, environment branches and diverged refs to the user. Use when a repo lives on both GitHub and GitLab and the two have drifted, or to check several such repos at once.
when_to_use: sync GitHub and GitLab, "sync 2 remote", "đồng bộ github và gitlab", mirror a branch to the other remote, "gitlab chưa có branch này", GitLab is behind GitHub, push tags to both remotes, check drift across many repos, /sync-remote
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/scripts/sync-remote.sh *)
---

# sync-remote — one repo, two hosts, no drift

**Invoke:** `/sync-remote [repo-dir …] [--remotes <a> <b>]`

A repo pushed to GitHub and GitLab by different people drifts: a branch exists on one side only, a fix landed on one side, a release tag never reached the other. This skill finds every difference and closes the safe ones. It never rewrites history: no force, no delete, no mirror push.

---

## Step 1 — Find the repos and their remotes

- No argument → the current repo. Directories given → each one. A parent folder → every direct child that is a git repo.
- Per repo, the script picks the first remote whose URL contains `github` and the first containing `gitlab`. `--remotes <a> <b>` names them instead (a self-hosted GitLab whose URL says neither).

**Done when:** each repo has two named remotes, or is listed as skipped with its `git remote -v`.

## Step 2 — Plan (read-only)

Run per repo: `bash ${CLAUDE_SKILL_DIR}/scripts/sync-remote.sh <repo-dir> [<a> <b>]`. It fetches both remotes into `refs/sync-remote/<remote>/…` (your local branches and tags are untouched) and prints one row per ref:

| Kind | Meaning | Action |
|---|---|---|
| `same` | both sides at one commit | none |
| `push` | one side is ahead (fast-forward), or the branch exists on one side only | Step 3 runs its command |
| `tag-push` | tag exists on one side only | Step 3 runs its command |
| `protected` | `main`/`master` or an environment branch (`HARNESS_ENV_BRANCHES`) | never pushed by Claude; the user runs the printed command or sets up mirroring |
| `diverged` | each side has commits the other lacks | never pushed; merge through a PR/MR on one side, then sync |
| `tag-conflict` | same tag name, different commits | never pushed; a person picks the right one |

Exit 3 → fewer than two matching remotes; exit 4 → not a repo or the fetch failed (auth, network). Report it and go on with the next repo.

Show one table for all repos: repo · in sync · to push · protected · diverged · tag conflicts. Below it, list each `push` row's detail; "only on X" may mean the other side **deleted** it, so name those rows separately.

## Step 3 — Confirm, then push one ref per command

Ask once through `AskUserQuestion`: *push all listed (Recommended)* / *push all except the "only on" branches* / *report only*. Then run each chosen row's command **as its own Bash call**, exactly as printed, so the branch-guard hook checks every push. Never batch them into a script or a loop, never add `--force`, `--mirror`, `--all` or `--delete`, never edit the refspec.

- A push rejected as non-fast-forward → someone pushed meanwhile; re-run Step 2 for that repo once.
- A push blocked by the branch-guard hook or by server protection → leave it; it moves to the user's list.

**Done when:** every chosen row is pushed or listed with the error it hit.

## Step 4 — Hand the rest to the user

One list per repo:

- `protected` rows: the printed command for the user to run themselves, since `git.md` forbids Claude pushing to those branches. Durable fix: configure **push mirroring** in GitLab (Settings → Repository → Mirroring repositories, direction push or pull, "Only mirror protected branches"), so main and the environment branches stay in sync without anyone pushing by hand.
- `diverged` rows: which side to merge into which, through a PR/MR (`/finish-branch`, ship).
- `tag-conflict` rows: both commits, and the question of which is the release.

Re-run Step 2 at the end; report the before/after counts.

**Done when:** a final table shows each repo's counts after the sync, and every remaining row has an owner.
