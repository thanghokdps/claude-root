# Infrastructure rules — read by devops-engineer and infra-change

- Plan before apply, every time: `terraform plan -out`, `kubectl diff`, `helm diff`. The plan is read as a reviewer; a destroy or a replacement of a stateful resource is a decision for the user, not a line in a log.
- Production is applied by a person or by the CI job on the protected branch. The `ship` plugin's `infra-gate` denies `terraform apply` / `destroy`, `kubectl apply` / `delete` / `scale` / `rollout`, `helm install` / `upgrade` / `uninstall` / `rollback` on a production context from a session, and asks before a non-production one. Relay a denial; never work around it with another context, workspace, namespace, alias or wrapper.
- The rollback is named before the apply: previous plan, `helm rollback` revision, previous manifest, and whether data survives it.
- Secrets by reference only (secret manager, `secretKeyRef`); never a value in `.tf`, values files or manifests.
- Least privilege: IAM policies and RBAC name the actions and resources; no `*`, no cluster-admin for a workload, workload identity / OIDC over static keys.
- Workloads declare resource requests and limits, readiness and liveness probes, a `PodDisruptionBudget` above one replica, and a pinned image tag or digest.
- Terraform state in a locked remote backend; one workspace or state file per environment; modules reused, not copied.
- Environments are promoted lowest first (dev → staging → production) with the same declaration and only the values changing.
