# Summary — <slug>

Lane: tiny | normal | high-risk
Confidence: high | medium | low
Reason: <one sentence — which flags fired, or "none">
Flags: <comma-separated risk flags, or `none`>
Input-type: new spec | spec slice | change request | new initiative | maintenance | harness improvement

> `Lane` drives **ceremony** (how much proof). `Confidence` drives **interruption** (whether human is asked).
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
