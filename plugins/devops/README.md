# devops

Role pack for CI/CD, containers and infrastructure: the `devops-engineer` agent that `/feature`, `/ticket` and `/fix-bug` dispatch pipeline, image and infra slices to, the three skills it runs, and the rules it reads on demand. Off by default; core's `repo-profile` hook turns it on in a repo that holds a `Dockerfile`, `docker-compose*`, `.github/workflows/`, `.gitlab-ci.yml`, `*.tf`, `k8s/` or `Chart.yaml`.

**For:** DevOps and platform engineers, and every `/feature` run that includes a CI job, an image or a cloud resource.

## Agent

`agents/devops-engineer.md` (sonnet) builds exactly one slice from the supervisor's brief — pipeline, image or resource, environments, files, the check that proves it — by running the skills below, and reports in three lines. Application code, app releases (`ship`'s `/release-checklist`) and real secrets are not its job.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/pipeline` | A CI job, workflow or deploy step in GitHub Actions / GitLab CI: the same gate script as local, actions pinned by SHA, least-privilege permissions, scoped secrets, lockfile-keyed caches, deploy only from the protected branch; proven green on the branch | "thêm job chạy test cho mỗi PR" · "pipeline chậm, cache node_modules" |
| `/container` | A Dockerfile or compose service: multi-stage, pinned base by digest, non-root, no secret in a layer, healthcheck, small context; proven by building, running and passing the healthcheck | "viết Dockerfile cho service này" · "image 1.2 GB, thu nhỏ lại" |
| `/infra-change` | A Terraform, Kubernetes or Helm change: plan → review → apply where allowed → verify, rollback named first; production applied by a person under `ship`'s `infra-gate` | "thêm bucket S3 cho upload" · "tăng replicas cho api trên staging" |

## Rules and the gate

`rules/ci.md`, `rules/container.md`, `rules/infra.md` — read by the agent and the skills, never always-loaded. The blocking hook `infra-gate` is in `ship`, not here: a gate must run before this pack is enabled, so every blocking hook of the kit lives in a process plugin.
