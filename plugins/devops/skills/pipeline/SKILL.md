---
model: opus
effort: high
name: pipeline
description: Adds or changes a CI/CD workflow or job in GitHub Actions or GitLab CI the way the repo already runs them — the same gate script locally and in CI, actions pinned by commit SHA, least-privilege token permissions, secrets from the platform store, caches keyed on lockfiles, a deploy step that cannot run from a fork. Proves it with the workflow green on the branch. Use when the user asks to add or edit workflow YAML — a CI job, a build or test workflow, a deploy step, a cache, permissions, or a slow pipeline's configuration.
when_to_use: add a CI job, "thêm job CI", GitHub Actions workflow, GitLab CI stage, "setup CI cho repo", run tests on pull requests, deploy step in CI, pipeline is slow, cache node_modules, pin actions by SHA, workflow permissions, CI secret, matrix build, edit the workflow yaml
---

# pipeline

**Invoke:** `/pipeline <what should run, when, and where it deploys>`

Rules: `${CLAUDE_PLUGIN_ROOT}/rules/ci.md`, `security.md` from core. A red build whose cause is the code, not the workflow, is `/ci-triage` (ship, if installed); a production deploy of an app is `/release-checklist` (ship, if installed).

---

## Step 1 — Detect

| Piece | Look for |
|-------|----------|
| Platform | `.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/` |
| The gate | the one script CI runs that developers also run locally (`scripts/check.sh`, `pnpm check`, `make test`) |
| Existing jobs | triggers, matrix, caches, reusable workflows / templates, environments and their protection rules |
| Secrets | names referenced as `${{ secrets.X }}` / CI variables; where they are set (repo, environment, org) |
| Runners | hosted vs self-hosted, OS, versions pinned in the workflow |

**Done when:** each row names a path. The change is stated as: trigger → jobs → what each job proves → where it deploys.

## Step 2 — Write the job the way the repo does

- One gate script, called the same way locally and in CI; CI never carries a check developers cannot run.
- Every third-party action pinned to a full commit SHA with the version in a comment; GitLab `include` pinned to a ref.
- `permissions:` at the top of the workflow set to the minimum (`contents: read` by default), widened per job only where needed.
- Secrets come from the platform store, scoped to an environment with required reviewers for production; never echoed, never passed through `pull_request` from a fork.
- Caches keyed on the lockfile hash; artifacts expire.
- A deploy job runs only on the protected branch or a tag, after the gate job, with `concurrency` so two deploys cannot overlap.

**Done when:** `actionlint` / `gitlab-ci-lint` (or the platform's validator) passes on the file.

## Step 3 — Prove it

Push the branch and read the run: the new job ran, took the expected time, its cache hit on the second run, and the deploy job was skipped on the branch. Quote the run URL and timings.

**Done when:** the workflow is green on the branch and the run's log shows the job did what Step 1 said.

---

Hand-offs: build errors from the code → `/fix-bug` · the image the job builds → `/container` · the infrastructure it deploys to → `/infra-change` · done → `/verify-done` → `/review-checklist`.
