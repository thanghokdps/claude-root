# Incident contract — `docs/incidents/<YYYY-MM-DD>-<slug>/`

Committed to the repo. `<YYYY-MM-DD>` is the day the incident started (UTC); `<slug>` names the symptom (`login-500`, `orders-duplicated`). One folder per incident.

## Severity

| Sev | Meaning | Examples | Postmortem due |
|-----|---------|----------|----------------|
| SEV1 | Core flow down for most users, or data loss / leak | login down, payments failing, PII exposed | 2 working days |
| SEV2 | Core flow degraded, or down for a segment | 20% of requests 5xx, one region, one tenant | 5 working days |
| SEV3 | Non-core flow broken, a workaround exists | export fails, a report is late | optional; a ticket is enough |

## `incident.md` — written during the incident

```markdown
# <slug>

Severity: SEV<n> · Status: investigating | mitigated | resolved · Lead: <name>
Started: <YYYY-MM-DD HH:MM UTC> · Detected: <time, how> · Mitigated: <time> · Resolved: <time>

## Symptom
<what users see, with the alert / dashboard / error link>

## Timeline (UTC)
| Time | Who | Observed / did |
|------|-----|----------------|
| 09:12 | alert | p95 > 5s on /api/orders |

## Mitigation
<action taken, and the evidence that users stopped being affected>
```

## `postmortem.md` — written after

```markdown
# Postmortem — <slug>

Severity: SEV<n> · Duration: <start → resolved> · Author: <name> · Reviewed by: <names>

## Summary
<three sentences: what broke, for whom, how it was fixed>

## Impact
- Duration: <minutes> · Users / requests affected: <n> · Data touched: <what> · Cost: <if known>

## Root cause
<the decision or missing guard, with evidence>

## Contributing factors
- <factor> — <evidence>

## Five whys
1. Why <symptom>? Because <…> (evidence)

## What went well · what went badly · where we got lucky
- …

## Action items
| # | Type | Action | Owner | Due | Link |
|---|------|--------|-------|-----|------|
| A1 | preventive / detective / mitigating | <action> | <one person> | <date> | <ticket> |

## Links
Fix PR: <link> · Regression test: <path> · Ticket(s): <links>
```
