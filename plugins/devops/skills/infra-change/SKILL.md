---
model: opus
effort: high
name: infra-change
description: Changes infrastructure declared in Terraform, Kubernetes manifests or Helm charts through plan → review → apply → verify, with the rollback named before the apply. Production is applied by a person — the ship plugin's infra-gate denies a production apply from the session and asks before a non-production one. Use when the user asks to add or change a cloud resource, a cluster workload, a Helm release, an ingress, a secret reference, or to roll back an infrastructure change.
when_to_use: terraform change, "sửa terraform", add a bucket or queue or database instance, kubernetes manifest, helm values, ingress, deployment replicas, hpa, "deploy lên k8s", terraform plan, apply to staging, rollback the release, drift between code and cloud
---

# infra-change

**Invoke:** `/infra-change <resource, environment, and the outcome>`

Rules: `${CLAUDE_PLUGIN_ROOT}/rules/infra.md`, `security.md` from core. Hard gate: every infra change is high-risk in `/coordinator`'s lanes. A destructive database change inside it (drop, resize, engine upgrade) is also `/write-migration` (ship, if installed).

---

## Step 1 — Detect

| Piece | Look for |
|-------|----------|
| Tool and layout | `*.tf` modules and environments (`envs/<env>/`, workspaces, `-var-file`), `k8s/` or `manifests/`, `Chart.yaml` + `values-<env>.yaml`, `kustomization.yaml` |
| State and context | the Terraform backend and lock, kube contexts and namespaces per environment, Helm release names |
| How changes land | applied by CI from the protected branch, or by hand; who may apply to production |
| Existing resource | the module or manifest closest to what is asked, its naming and tags |

**Done when:** each row names a path, and the environments the change touches are listed with how each is applied.

## Step 2 — Change the declaration

- Reuse the repo's module or chart; a new one only when none fits, and it follows the same inputs, naming and tags.
- Secrets by reference (secret manager ARN, `secretKeyRef`), never a value; least-privilege IAM / RBAC, no wildcard actions or cluster-admin for a workload.
- Workloads: resource requests and limits, readiness and liveness probes, a `PodDisruptionBudget` for anything with more than one replica, no `latest` image tag.
- Terraform: `terraform fmt`, `validate`, and the repo's policy checks (`tflint`, `checkov`, `conftest`) pass.

**Done when:** the linters pass and the diff touches only the resources Step 1 named.

## Step 3 — Plan and review

Run the read-only preview for each environment, lowest first: `terraform plan -out`, `kubectl diff`, `helm diff upgrade` (or `helm template` piped to `kubectl diff`). Read it as a reviewer: every create, update and destroy expected, no replacement of a stateful resource, no change outside the slice. Name the rollback before going on: the previous plan, `helm rollback <release> <revision>`, or the previous manifest, and whether data survives it.

**Done when:** the plan summary and the rollback are quoted; a destroy or replacement of a stateful resource stops here for the user's decision.

## Step 4 — Apply where allowed, then verify

- Non-production: apply from the saved plan (`terraform apply plan.out`, `kubectl apply`, `helm upgrade --install --atomic`); the gate asks once. Then verify the resource: rollout status, the health route, the metric or log that proves it.
- Production: hand the exact command and the saved plan to the user, or to the CI job that applies from the protected branch. The gate denies a production apply from the session; never retry with another context, workspace, namespace or wrapper.

**Done when:** the non-production environment shows the change live, and production has either the person's apply recorded or the PR that CI will apply.

---

Hand-offs: the CI job that applies it → `/pipeline` · the image it runs → `/container` · an outage during the change → `/incident` (ship, if installed) · done → `/verify-done` → `/review-checklist` → `/docs-sync`.
