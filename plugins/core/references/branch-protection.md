# Branch protection on the server

The `branch-guard` hook and `rules/git.md` stop Claude pushing to `main` and the environment branches from this machine. A teammate's laptop, a CI token or another tool is stopped only by the server, so every repo with a remote gets server rules too. Read by `/project-init` (Step 1c).

## GitHub — rulesets

Templates in `${CLAUDE_PLUGIN_ROOT}/templates/github/`:

| File | Covers | Rules |
|------|--------|-------|
| `ruleset-default-branch.json` | the default branch (`~DEFAULT_BRANCH`) | no deletion, no force-push, PR with 1 approval and resolved threads, required checks |
| `ruleset-env-branches.json` | `dev develop stag stage staging prod production` | the same |

Both let admins bypass **only through a PR** (`bypass_mode: pull_request`): an admin may merge without the approval, never push directly. A repo's existing env-branch names other than these are added to `include` as `refs/heads/<name>`, after asking.

### Steps

1. **Remote** — `git remote get-url origin`. No remote → skip, and say to re-run `/project-init` once it exists. GitLab → § GitLab. Anything else → print the rules to set by hand and stop.
2. **Existing rules** — `gh api repos/<owner>/<repo>/rulesets --jq '.[].name'` and, for the default branch, `gh api repos/<owner>/<repo>/rules/branches/<default> --jq '[.[].type]'`. A ruleset or classic protection that already blocks direct pushes there → skip that template, and report what exists.
3. **Permission** — `gh api repos/<owner>/<repo> --jq .permissions.admin`. Not admin → print the filled JSON and the `gh api` command for an admin; do not try.
4. **Required checks** — the check-run names on the default branch's last commit: `gh api repos/<owner>/<repo>/commits/<default>/check-runs --jq '[.check_runs[].name] | unique'`. Replace the `__CHECK__` entry with one `{"context": "<name>"}` per check. No check runs yet → drop the `required_status_checks` rule and say CI must be added to it later.
5. **Ask** — show the filled JSON of each template still needed, then one `AskUserQuestion`: *Apply both (Recommended)* · *Only the environment branches* · *Skip*. Never apply unasked: a ruleset changes who can merge in a shared repo.
6. **Apply** — `gh api -X POST repos/<owner>/<repo>/rulesets --input <filled file>` per chosen template, then confirm with `gh api repos/<owner>/<repo>/rules/branches/dev --jq '[.[].type]'` (and the default branch).

**Done when:** each chosen ruleset is `active` and `rules/branches/<name>` lists `pull_request` for the default branch and `dev`; or the skip and its reason are in `.claude/docs/index.md` under Known constraints.

## GitLab — protected branches

`glab api projects/:id/protected_branches` lists what exists. For each of the default branch and the environment branches (wildcards such as `stag*` work):

```bash
glab api -X POST projects/:id/protected_branches -f name=<branch> -f push_access_level=0 -f merge_access_level=40 -f allow_force_push=false
```

`push_access_level=0` is "No one"; `40` is Maintainers. Add "Pipelines must succeed" in the project's merge settings. Same ask-first rule as above.
