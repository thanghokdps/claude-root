# Spec artifact templates — read by /coordinator at Step 4b (high-risk lane only)

`specs/<slug>/SUMMARY.md`
```markdown
# Summary — <slug>

Lane: <tiny|normal|high-risk>
Confidence: <high|medium|low>
Reason: <one sentence — which flags fired, or "none">
Flags: <comma-separated risk flags, or `none`>
Input-type: <new spec | spec slice | change request | new initiative | maintenance | harness improvement>

> `Lane` drives ceremony (how much proof). `Confidence` drives interruption (whether human is asked).
> A hard gate forces `high-risk`. Low confidence escalates regardless of lane.

## What changed

<filled by Implementer / Debugger / Refactorer after completing work>

## Rationale

<filled by Planner>

## Alternatives considered

- none

## Deviations

- none

## Verify

| Check | Command | Exit | Notes |
|-------|---------|------|-------|
| <unit/lint/build/behaviour> | `<command>` | 0 | |

## Rollback

- `git revert <sha>`

## Harness-Delta

- none
```

---

`specs/<slug>/TEST_MATRIX.md`
```markdown
# Test Matrix — <slug>

## Status values

| Status | Meaning |
|--------|---------|
| planned | Accepted as intended, not yet implemented |
| in_progress | Actively being built |
| implemented | Implemented and proof exists |
| changed | Contract changed after earlier implementation |
| retired | No longer part of the contract |

## Matrix

| Behavior | Contract | Unit | Integration | E2E | Status | Evidence |
|----------|----------|------|-------------|-----|--------|----------|
| <describe expected behavior> | yes | no | no | no | planned | none |

## Evidence rules

- **Unit** — pure domain/application logic
- **Integration** — backend enforcement, data integrity, provider/job/service contracts
- **E2E** — user-visible end-to-end flows
- A row may ship without every column if SUMMARY.md explains why (e.g. tiny lane)
- `Evidence` points at proof: test path, `Verify` row, or commit sha — never `none` for `implemented`
```

---

`specs/<slug>/ESCALATIONS.md`
```markdown
# Escalations — <slug>

Default: **deny-on-no-response**. No recorded decision → work stays blocked.

---

<!-- Add entries below only when a hard gate fires, confidence is low, or scope is ambiguous -->

<!--
E001
- raised_by: <orchestrator | agent name>
- date: <YYYY-MM-DD>
- trigger: hard-gate | low-confidence | ambiguous-direction | in-flight | system-redefinition
- question: <one sentence — the decision needed>
- context: <one line — what work is blocked on this>
- options:
    - A) <option + consequence>
    - B) <option + consequence>
- default_if_no_response: BLOCK
- decision: pending
- decided_by:
- decided_at:
-->
```

---

**Agent responsibilities for specs files:**

| Agent | SUMMARY.md | TEST_MATRIX.md | ESCALATIONS.md |
|---|---|---|---|
| Coordinator | Fill header (lane, confidence, flags) | Create skeleton rows | Create file (entries only if needed) |
| Planner | Fill Rationale + Alternatives | Add planned rows | Add entry if direction is ambiguous |
| Implementer / Debugger / Refactorer | Fill "What changed" + Verify table | Update status → `implemented`, add Evidence | Add entry if blocked |
| Verifier | Confirm Verify table passes, add commit sha | Mark rows `implemented` | — |
| Security Reviewer | Add findings to Verify table | — | Add entry if hard gate fires |
