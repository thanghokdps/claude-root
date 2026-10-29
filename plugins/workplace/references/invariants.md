# Workplace invariants — what must hold in an internal HR / workplace app

Read by `/workplace-review`, and by planning skills when the repo profile says `Domain: workplace`. Distilled from real request, booking and approval code. The *Seen* lines are failures that shipped there; check for each one.

## 1. Requests and their states

- One state machine per request type, written down: `pending → approved | rejected`, `pending | approved → cancelled`, plus type-specific states (`processing → done | closed` for maintenance). Every transition names who may make it.
- The server enforces the matrix. A transition not in it is rejected, never silently applied.
- A repeated identical decision is a no-op; a conflicting second decision either is an explicit re-decision (recorded) or fails. Pick one per type and say which.
- Status strings are one shared enum used by server and clients. *Seen:* client `canceled` vs server `cancelled`, so cancelled slots stayed in the client cache.
- Auto-approved types (a room booking, a past-dated change) are a deliberate rule in one place, not a side effect of skipping a step.

## 2. Who may act — record level, every time

- **Every decision endpoint checks that the caller is an approver of this record.** Visibility checks in the list or detail view do not protect the outcome endpoint. *Seen:* approver membership checked for display, not on the decision path.
- Only the requester (or the person who filed it for them) cancels; an approver rejects instead.
- Identity comparisons normalise once (lower-cased email or a stable user id) everywhere. *Seen:* approver check case-sensitive while list filters lower-cased.
- A request filed for someone else records both people; both see it, only the filer edits it.
- Approvers a requester may add themselves are a policy decision, not a default. *Seen:* the requester could add arbitrary approvers to their own booking.
- Manager scope comes from one source (org chart, relationship table); "manager sees team" is a query filter on the server, never a client filter.
- Reading one record by id checks ownership or scope too, not only the role middleware.

## 3. Balances

- Unit and rounding are stated: days or hours, half-day value, what a partial day counts as.
- Working days are defined once (weekends, public holidays, make-up working days, per office if offices differ). Two code paths counting days differently is a bug. *Seen:* one service charged weekends and holidays, another counted business days only.
- When a request is counted: on approve (not on submit), restored on cancel or reject. Pending requests are held against the balance at submit time, or several pending requests can together exceed it. *Seen:* submit compared against approved-only remaining.
- Negative balance is either blocked at submit or an explicit policy (unpaid leave, borrowing), never a display clamp to 0.
- Carry-over, accrual and expiry live in code or config with a test, not only in a policy document or eval data.

## 4. Bookings and reservations

- Overlap is `start1 < end2 && start2 < end1` (back-to-back allowed), checked **on the server in the same transaction as the insert**, or by a DB exclusion/unique constraint. *Seen:* read-then-write with no lock, so two requests for one slot both passed.
- The server rejects `start >= end`, a start in the past and a slot outside bookable hours. Client-only checks are hints. *Seen:* every one of these enforced only in the mobile picker.
- Capacity, buffer time and recurring slots are either modelled or explicitly out of scope.
- Deleting or replacing a resource (room, scope, office) checks for live bookings or tickets that reference it. *Seen:* a config PUT deleted rooms missing from the payload; deleting a maintenance scope broke later decisions on its tickets.

## 5. Time and cutoffs

- One business time zone per office, from config; dates computed in it on the server. Client device time is display only. *Seen:* a client computed cutoffs on the device clock while the server used its own zone.
- Date-only values (holidays) and instants (slot start) are different types; never parse a date-only value as UTC midnight and compare it with a local instant.
- Every cutoff (order meals by, cancel by, book up to N days ahead) is a named server constant with a test at the boundary minute. A rule only in the picker is not a rule.

## 6. Side effects and notifications

- A decision that changes other data (leave approved → cancel meal orders, reallocation → reschedule jobs) does it in one place, reversibly: reject or cancel undoes exactly what approve did.
- Notifications are sent after commit, are idempotent per (record, event, recipient), and a failed send is logged or retried — never swallowed. *Seen:* push errors caught and discarded, no retry, no record.
- Each event names its recipients (requester, approvers, observers, cc); "who is told on cancel" is decided, not left out.
- Scheduled reminders have a stop condition and a maximum count.

## 7. Audit and personal data

- Every decision writes an audit row: actor, action, record, note, time. A required note (reject, close) is enforced on the server.
- Admin edits to employee data, roles and configuration are audited too.
- Employee personal fields (name, birthday, phone, address, email) are listed; each is either encrypted, masked or justified. Lookups on encrypted fields use a keyed hash column.
- Admin is a role in data, not only an environment allowlist of emails.
- Deactivated employees cannot sign in, and requests that name them as approver are reassigned.

## 8. Gaps to ask about when the code has none

Delegation while an approver is away · escalation or expiry of stale requests · multi-office or multi-time-zone staff · HR system sync for the org chart · localisation. Each is a need question (`domain-questions.md`), never a silent default.
