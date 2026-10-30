# ship

Land and release: close a finished branch, read a red build, walk a release through its checklist, write a migration that can run while old code still runs, run an incident, and keep two remotes in sync.

**For:** release and CI owners, and any developer at the end of a branch.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/finish-branch` | The plan's tasks are done and the work needs to land or be parked. Verifies, then offers merge, open PR/MR, keep or discard, and cleans up the worktree and local branch | "wrap this up and open the MR" |
| `/ci-triage` | A pipeline, Action or job is red and the cause is unknown. Classifies it as regression, flaky or environment with a one-sentence root cause, the evidence and the next action | "why is the build red? is this flaky?" |
| `/release-checklist` | Cutting a release, tagging a version, deploying to staging or production. Scope frozen → gates green → migrations safe → notes → tag → deploy → smoke → rollback ready; stops on the first unmet item | `/release-checklist 1.4.0` |
| `/write-migration` | Adding, renaming or dropping a table, column, index or constraint, or backfilling data. Expand/contract, non-locking, backfill separated, down path tested. Always the high-risk lane | "rename the `status` column without downtime" |
| `/incident` | Production or staging is down, degraded, losing or leaking data. Timeline and severity, mitigate before any code fix, then root cause, regression test and a blameless postmortem in `docs/incidents/<date>-<slug>/` | "prod sập, 5xx tăng vọt" |
| `/sync-remote` | A repo lives on both GitHub and GitLab and they drifted. Classifies every branch and tag, pushes fast-forwards and missing tags after one confirmation, leaves `main`, environment branches and diverged refs to you | "đồng bộ github và gitlab" |

## Hooks

| Hook | Event | Does |
|---|---|---|
| `infra-gate` | before Bash, only in a repo with `*.tf`, `k8s/`, `manifests/`, `Chart.yaml`, `kustomization.yaml` or `.claude/infra-gate.json` | Production infrastructure is applied by a person: `terraform apply`, `kubectl apply` / `delete` / `scale` / `rollout`, `helm install` / `upgrade` / `rollback` on a production workspace, var-file, context or namespace are denied; `terraform destroy` and cluster-scope deletes always; the same mutations on a non-production or unnamed target ask first; `eval`, `sh -c` and `xargs` around them are denied. Read-only `plan` / `diff` / `get` / `template` pass. Config: `.claude/infra-gate.json` → `{"production": ["prod", "production", "live"]}`. Skills: `/infra-change` (devops, if installed) |
| `release-gate` | before Bash, only in a repo with `eas.json` or `.claude/release-gate.json` | A production `eas build`, `eas submit`, `eas update` or a `v*` tag push ships only the exact commit of a `release/<version>` PR/MR approved by someone other than its author. Approving a PR/MR from the session is always denied. Mobile steps: `/release-checklist` → `references/mobile.md` |

## Depends on

`core` (and through it `progress`).

## Install

```text
/plugin install ship@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
