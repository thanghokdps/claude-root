# CI/CD rules — read by devops-engineer and pipeline

- One gate script, run the same way locally and in CI. CI never carries a check developers cannot run; a check added to CI is added to the script.
- Third-party actions pinned to a full commit SHA (version in a comment); GitLab includes pinned to a ref. A floating tag is a supply-chain hole.
- `permissions:` declared at the workflow top, `contents: read` by default, widened per job only for what that job does (`id-token: write` for OIDC, `pull-requests: write` for a commenting job).
- Secrets from the platform store, scoped to an environment with required reviewers for production. Never printed, never interpolated into a shell string from untrusted input (PR titles, branch names, issue bodies); never available to `pull_request` runs from forks.
- Caches keyed on the lockfile hash and the toolchain version; artifacts with a retention period.
- Deploy jobs run on the protected branch or a tag only, after the gate job, with `concurrency` per environment so two deploys cannot overlap, and with OIDC rather than long-lived cloud keys.
- A matrix covers the versions the project supports, nothing more; a slow job is split or cached before a bigger runner is bought.
- Workflow files are linted (`actionlint`, `gitlab-ci-lint`) in the gate script.
