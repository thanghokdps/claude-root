# Model cost — Opus decides, cheaper models do the typing

Save cost without losing judgement: the main session (on Opus) plans, decides and reviews; work it hands to a subagent runs on the cheapest model that can do it.

| Work | Model |
|---|---|
| Architecture, plans, trade-offs, review, root cause, security, anything a wrong call makes expensive | `opus` (the main session, or an advisor subagent) |
| Writing or changing code from an approved plan or slice | `sonnet` |
| Mechanical work: rename, format, constants, types from a schema, fixture data, boilerplate tests from a written test matrix, simple CRUD | `haiku` |
| Searching or reading many files to report back | `haiku` (`Explore`) |

Skills follow the same split. A skill whose wrong call is expensive (plans, architecture, review, security, migrations, root cause) pins `model: opus`. A light skill (`/btw`, `/compact`, `/sync-memory`, `/verify-done`, `/checkpoint`, `/create-pr`, `/finish-branch`, `/release-checklist`, `/sync-remote`) sets no model and runs on the session's model, so the user's plan and budget decide.

- Set `model` on every Agent call you dispatch; never leave it to inherit Opus for coding or mechanical work.
- Write the brief so the cheaper model has nothing left to decide: files, the contract, the test to make pass, the done check.
- A subagent that reports it is stuck, or fails the same check twice, goes back to Opus: re-plan, then re-dispatch. Never retry the same brief on the same model a third time.
- Review and verification of a cheaper model's diff stays on Opus.
- The user naming a model overrides this table.
