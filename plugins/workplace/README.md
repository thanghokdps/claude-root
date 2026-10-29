# workplace

Domain pack for internal workplace / HR apps: time off, approvals, leave balances, room and resource bookings, meal reservations, maintenance requests. Adds the domain's rules on top of the general kit; it never replaces a role plugin.

## How it turns on

Off at user scope after `bash scripts/install.sh`. Core's `repo-profile` hook enables it in a repo's `.claude/settings.local.json` (effective next session) when the repo has a `Domain: workplace` line in `docs/requirements.md` or `.claude/docs/index.md` (`/kickoff` writes it), or two or more HR module folders under `apps/`, `src/modules/` or `src/features/`. An explicit `false` in project or local settings wins.

Also installs: `progress`.

## Contents

| Part | Does |
|------|------|
| `/workplace-review` | Reviews a plan or diff touching requests, approvals, balances or bookings against the domain invariants; findings with the failing case, the fix and the cost of skipping it |
| `references/invariants.md` | The rules: state machine, approver check on every decision, balances, server-side overlap and cutoffs, time zones, notifications, audit, personal data — with failures seen in real code |
| `references/domain-model.md` | Starter entities and ERD for `/domain-model` and `/db-change` |
| `references/domain-questions.md` | Domain need questions for `/kickoff` and `/brainstorming` |
