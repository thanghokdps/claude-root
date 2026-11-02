# Git

- One logical change per commit. Message: `<type>: <imperative what/why>` ≤72 chars; types `feat fix refactor test docs chore perf ci`.
- No `Co-Authored-By` (Claude/AI), `Claude-Session` or "Generated with" trailers in commits or PR bodies.
- Branch first: `<type>/<short-slug>`; never commit to `main`/`master` or an environment branch (`dev`, `develop`, `stag`, `stage`, `staging`, `prod`, `production`). The `branch-guard` hook blocks it; the only exception is the first commit of an empty repo, which the user then pushes.
- Add a remote in the form this machine already uses (an SSH alias from `~/.ssh/config` or another repo's `origin`), never HTTPS by default.
- Never push directly to those branches, in any repo, whatever its own config says: push the feature branch and open a PR. The core `branch-guard` hook blocks it locally; `/project-init` offers the GitHub rulesets that block it on the server.
- Stage specific files (`git add <paths>` / `-p`), check `git diff --staged` before committing. Never `--no-verify` unless asked.
- Never commit: `.env*` / secrets, `console.log` / `debugger` / `breakpoint()`, commented-out code, build artifacts, files >5MB.
- No amend or force-push on pushed/shared branches; rebase only private branches.
- Confirm first: `push --force`, `reset --hard` with changes, `clean -f`, merging a PR with `--admin`.
- PR/MR description says WHY + how tested; one feature per PR; CI green before merge.
