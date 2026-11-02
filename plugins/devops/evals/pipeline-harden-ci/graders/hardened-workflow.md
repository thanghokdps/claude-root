---
type: llm
focus: trace
---

Judge the workflow the run wrote, attempted or proposed. An Edit or Write tool input counts even when the sandbox denied it, and so does a full workflow given in the final reply.

The original has `actions/checkout@v4` unpinned, no `permissions:` block, a `pull_request_target` trigger, and a deploy job with no guard against forks or non-protected branches. The repo's gate is `scripts/check.sh`.

PASS if the new workflow pins every third-party action to a full 40-character commit SHA, sets `permissions:` to least privilege (such as `contents: read`), restricts the deploy job to the protected branch (and not to fork pull requests), and adds a pull-request test job that runs `./scripts/check.sh` rather than separate inline `npm` commands.
FAIL if any action stays on a tag only, `permissions:` is missing, deploy can still run for a fork PR, or the test job re-implements the checks instead of calling scripts/check.sh.
