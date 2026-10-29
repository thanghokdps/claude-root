---
model: opus
effort: high
name: workplace-review
description: Reviews a plan or diff in an internal HR / workplace app — time off, approvals, leave balances, room or resource bookings, meal reservations, maintenance requests — against the domain's invariants (state machine, approver check on every decision, balance math, server-side overlap and cutoffs, business time zone, idempotent notifications, audit, employee personal data) and returns numbered findings with the case that fails, the fix and the cost of skipping it. Use before the PR of any change to requests, approvals, balances or bookings.
when_to_use: change to time off or leave, approve or reject flow, leave balance, room booking, desk or resource booking, meal reservation, maintenance ticket, "review the approval flow", "check the booking logic", "duyệt đơn nghỉ phép", "đặt phòng họp bị trùng", before the PR in a repo whose profile says Domain workplace
---

# workplace-review — domain review for request, approval and booking code

**Invoke:** `/workplace-review [plan path | PR number | branch]` — default: current branch vs its base.

General review (`/review-checklist`, review, if installed) finds what any code gets wrong. This one finds what HR and workplace apps get wrong: an outcome endpoint without an approver check, overlap checked only in the picker, a cutoff on the device clock. The rules are `${CLAUDE_PLUGIN_ROOT}/references/invariants.md`; read it before Step 1.

---

## Step 1 — Map the change to the domain

From the diff or plan, list each request type, booking type, balance and side effect it touches, and the files that hold its state transitions, decision endpoint, validation and notifications. Open each file; a remembered file is not evidence.

**Done when:** every touched domain object has its files listed, or the change touches none (then say so and stop).

## Step 2 — Check each invariant section that applies

Walk `invariants.md` §§ 1–7 for the objects from Step 1. For every rule, find the line that enforces it **on the server**, or the case that breaks it. Client-only enforcement counts as missing. Check every *Seen* line explicitly.

**Done when:** each applicable rule is marked held (`file:line`) or broken (the failing case).

## Step 3 — Report

First send every broken rule through `${CLAUDE_PLUGIN_ROOT}/references/refute.md`. Only `confirmed` findings are numbered. A `needs_validation` finding goes under **Not covered** with its missing fact. A `rejected` one goes on a `Rejected:` line with the line that holds the rule.

Numbered findings, most severe first. A broken § 2 (who may act) or § 7 (audit, personal data) rule is a hard gate: it puts the change in the high-risk lane.

```
1. <rule, short> — <file:line>
   Fails when: <concrete input or sequence → wrong result>
   Fix: <the change>
   Skip cost: <what happens in production>
```

Then a **Not covered** line for rules with no evidence either way, and § 8 gaps the change depends on, each as a need question from `${CLAUDE_PLUGIN_ROOT}/references/domain-questions.md` — asked one per turn, never defaulted silently.

**Done when:** every broken rule is a finding with its failing case, and the user has seen the report.

---

## Rules

- Never pass a rule because the UI prevents it; the server is the boundary.
- Never invent a policy (approver rules, cutoffs, leave units): when the code and the requirements are silent, it is a need question.
- Findings in another repo the change does not touch are reported, never fixed here.
