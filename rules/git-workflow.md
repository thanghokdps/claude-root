# Git Workflow Rules

Universal git rules for all projects.

## Commits

- **One logical change per commit** — not one file, not one session
- **Commit message format**: `<type>: <description>` (or project-specific format from CLAUDE.md)
  - Types: `feat` `fix` `refactor` `chore` `docs` `test` `perf` `ci`
  - Description: imperative mood, ≤ 72 chars — "add dark mode" not "added dark mode"
- **Never commit**:
  - `.env`, `.dev.vars`, secret files
  - `console.log`, `debugger`, `pdb.set_trace()`
  - Commented-out code blocks
  - Generated files that are gitignored

## Branches

- Feature branches: `feat/<short-description>` or `feat/#<issue>-<description>`
- Bug fix: `fix/<short-description>`
- Never commit directly to `main` or `master` or `dev`
- Delete branches after merge — no zombie branches

## Staging

- `git add <specific files>` — never `git add .` or `git add -A` without reviewing diff
- Run `git diff --staged` before every commit to verify what's included
- If a file has both related and unrelated changes: `git add -p` to stage hunks

## History hygiene

- No `git commit --amend` on pushed commits — create a new commit instead
- No `git push --force` except on personal feature branches — never on shared branches
- Rebase local branch before PR — don't merge main into feature branches repeatedly

## Pull Requests

- PR description explains WHY, not what (the diff shows what)
- Link to the issue/ticket
- Keep PRs focused — one feature/fix per PR
- All CI checks must pass before merge
- At least one reviewer approval before merge to main

## Hard gates (always require confirmation)

- `git push --force` or `git push -f` on any shared branch
- `git reset --hard` with unstaged changes present
- `git clean -f` (deletes untracked files)
- `git push origin main` / `git push origin master`
