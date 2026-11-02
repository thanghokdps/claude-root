---
model: opus
effort: high
name: incident
description: Runs a production incident from the first alert to the postmortem. While it burns, it keeps a timestamped timeline, sets the severity, and mitigates (rollback, flag off, scale) before any code fix; afterwards it finds the root cause, locks it with a regression test, and writes a blameless postmortem to docs/incidents/<date>-<slug>/ with owned action items. Use when production or staging is down, degraded, losing data or leaking data, or when the user asks for an incident report or postmortem.
when_to_use: production is down, "prod sập", "sự cố production", outage, 5xx spike, users cannot log in, data loss, data leak, alert firing, on-call page, "viết postmortem", incident report, RCA, root cause analysis of an outage
---

# incident — Mitigate first, then find out why, then write it down

**Invoke:** `/incident [what is broken | alert link]` · `/incident postmortem <id>` for an incident already over.

Stopping the damage beats understanding it. Every minute spent on a root cause while users are failing is a minute of outage, so this skill mitigates first and debugs after. The record is written as it happens, because memory after the fact is wrong.

The contract (`incident.md`, `postmortem.md`) and the severity table are in `${CLAUDE_SKILL_DIR}/references/contract.md`. Read it before Step 1.

---

## Step 1 — Open the record

Create `docs/incidents/<YYYY-MM-DD>-<slug>/incident.md` from the template on a branch `fix/incident-<slug>`. Set the severity from the table (when unsure, pick the higher one) and name the incident lead; the lead is the user unless they say otherwise. Every action from here on is a timeline line with UTC time, who, and what was observed or done.

**Done when:** the file exists with severity, lead, the first symptom and its time.

## Step 2 — Mitigate before fixing

Pick the fastest action that stops the damage, in this order, and ask before any of them (each changes production):

1. Roll back the last deploy or config change, if the timeline makes it a suspect.
2. Turn the feature flag off, or route traffic away from the failing path.
3. Scale, restart, or fail over, for capacity or a stuck process.
4. A hotfix — only when none of the above can stop it.

Data loss or a data leak → also stop the write path or the exposure first, and tell the user who must be informed (security, legal, customers) per their policy. Never delete evidence: logs, traces and the bad data stay.

**Done when:** users are no longer affected, proven by the metric, the error rate or a real request — not by "the deploy finished".

## Step 3 — Root cause

Now debug, with the pressure off: `/fix-bug` (dev, if installed) builds the red loop from the incident's evidence. A red CI build in the chain → `/ci-triage`. Ask "why" until the answer is a decision or a missing guard, not a person: five whys, each with its evidence in the timeline.

**Done when:** the root cause and every contributing factor are written with their evidence, and a test reproduces the failure (red).

## Step 4 — Fix and lock it

The permanent fix goes through the normal path: a PR with the regression test (red before, green after), `/verify-done`, review. A schema or data repair → `/write-migration`. Mark the incident resolved only when the fix is deployed and the mitigation is undone (flag back on, traffic back), with the metric shown.

**Done when:** the fix is merged or its PR is open with green checks, and the incident status is `resolved`.

## Step 5 — Postmortem

Write `postmortem.md` beside `incident.md` from the template, within the severity's deadline:

- Blameless: systems and decisions, never "X forgot". A human error is a missing guard.
- Impact in numbers: duration, users or requests affected, data touched, money if known.
- What went well, what went badly, where we got lucky.
- Action items: each with one owner, a due date and a tracker link — preventive (stop it recurring), detective (notice sooner), mitigating (recover faster). An item without an owner is a wish; ask for one.

Commit both files in the fix PR, or in their own PR when the fix shipped as a hotfix. Link the postmortem from the tracker and from any `docs/tickets/<id>/` it changes.

**Done when:** `postmortem.md` is committed, every action item has an owner and a link, and the user has reviewed it.
