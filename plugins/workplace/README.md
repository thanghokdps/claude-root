# workplace

Domain pack for internal workplace and HR apps: time off, approvals, leave balances, room and resource bookings, meal reservations, maintenance requests. It adds the domain's rules on top of the general kit and never replaces a role plugin.

**For:** teams building or maintaining an internal HR / workplace app. Off by default; core's `repo-profile` hook turns it on in the repos that need it.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/workplace-review` | Before the PR of any change to requests, approvals, balances or bookings. Checks the plan or diff against the domain invariants (state machine, approver check on every decision, balance math, server-side overlap and cutoffs, business time zone, idempotent notifications, audit, employee personal data) and returns numbered findings with the failing case, the fix and the cost of skipping it | "duyệt đơn nghỉ phép" · "đặt phòng họp bị trùng, check giúp logic" |

The references the skills read: `references/invariants.md` (the rules, with failures seen in real code), `references/domain-model.md` (starter entities and ERD for `/domain-model` and `/db-change`), `references/domain-questions.md` (need questions for `/kickoff` and `/brainstorming`).

## Hooks

None of its own. It is enabled per repo by core's `repo-profile` hook when the repo has a `Domain: workplace` line in `docs/requirements.md` or `.claude/docs/index.md` (`/kickoff` writes it), or two or more HR module folders under `apps/`, `src/modules/` or `src/features/`. The switch is written to `.claude/settings.local.json`, effective next session; an explicit `false` in project or local settings wins.

## Depends on

`progress`.

## Install

```text
/plugin install workplace@harness
```

Usually not needed by hand: `scripts/install.sh` installs it off at user scope and `repo-profile` enables it per repo. The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
