# Git

- One logical change per commit. Message: `<type>: <imperative what/why>` ≤72 chars; types `feat fix refactor test docs chore perf ci`.
- No `Co-Authored-By` (Claude/AI), `Claude-Session` or "Generated with" trailers in commits or PR bodies.
- Branch first: `<type>/<short-slug>`; never commit to `main`/`master`/`dev`.
- Stage specific files (`git add <paths>` / `-p`), check `git diff --staged` before committing. Never `--no-verify` unless asked.
- Never commit: `.env*` / secrets, `console.log` / `debugger` / `breakpoint()`, commented-out code, build artifacts, files >5MB.
- No amend or force-push on pushed/shared branches; rebase only private branches.
- Confirm first: `push --force`, `reset --hard` with changes, `clean -f`, pushing to `main`/`master`.
- PR/MR description says WHY + how tested; one feature per PR; CI green before merge.
