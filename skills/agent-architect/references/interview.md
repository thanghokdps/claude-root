# Architecture interview — question bank

Ordered by blast radius: each answer narrows the ones after it. Skip any question the repo or the user's message already answers — facts are looked up, never asked.

| # | Question | Forks |
|---|----------|-------|
| 1 | **Host** — Node server/container, or Workers/edge? | Node → shape A possible (CopilotRuntime). Edge → shape B (own AG-UI emitter), edge-safe imports only |
| 2 | **Clients** — web React, mobile (headless), chat channel (Slack/Teams), API only? | Web → CopilotKit v2 hooks. Headless → state/custom-event contract. Channel → interrupt as a custom event + card |
| 3 | **Agent shape** — one agent, a supervisor over several, or a fixed workflow? | `shapes.md` decision rule; count tools per agent |
| 4 | **Writes** — does any tool change data? | Yes → deterministic HITL gate + pending-action ledger + confirm/cancel; one active action per thread |
| 5 | **Identity** — where does verified identity enter, and how do tools read it? | Token verify at the edge → server-injected claims → tools read trusted context; token in request scope only |
| 6 | **Persistence** — checkpoint per thread or per run? Where is the history's source of truth? Long-term memory? | Thread-scoped (durable state) vs run-scoped (history table is truth, checkpoints deleted at run end) |
| 7 | **Models** — providers, fallback order, caller-supplied keys, a cheap model for router/summary/suggestions? | Fallback middleware vs cascade model; key in request scope only |
| 8 | **Observability & privacy** — tracing provider, masking, retention, compliance controls? | Masked-by-default tracing; HMAC user ids |
| 9 | **Evals** — which behaviours are must-pass, which judge model, where does the CI gate sit? | Eval tree separate from unit tests; baseline diff gate |

## Shape of each question

```
**Q<n> — <one-line question>**

Why this matters: <what forks downstream>

My recommendation: <answer + reason, citing repo facts>
```

One question per turn. A weak answer ("later", "should be fine") gets one hard push, then is recorded as a decision with its stated risk.

## Output

`docs/adr/0001-agent-architecture.md`:

```markdown
# ADR 0001 — Agent architecture
Status: accepted · Date: <YYYY-MM-DD>

## Architecture card
Shape: A | B | hybrid · Host: · Transport: · Clients:
Agents: <id → purpose → tool count>
Writes/HITL: · Identity: · Checkpoints: · Memory:
Models: <primary → fallback; router/summary model>
Tracing: <provider, masking> · Evals: <must-pass list, gate>

## Decisions
| # | Decision | Reason | Ladder rung (L0–L3) |

## Rejected alternatives
## Revisit when
```
