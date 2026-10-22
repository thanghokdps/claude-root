# Architecture interview — question bank

Ordered by blast radius: each answer narrows the ones after it. Skip any question the repo or the user's message already answers — facts are looked up, never asked.

## The problem first (P1–P4) — before any technology

The assistant is built from these answers: every task in P2 must end up owned by an agent and a tool, every system in P3 by a tool, every line of P4 by a boundary rule or an eval.

| # | Question | Becomes |
|---|----------|---------|
| P1 | **Who and why** — who uses it, and what problem does it solve, in one sentence? | Agent purpose, system prompt opening line |
| P2 | **Top tasks** — the 3–5 things users will ask, each with one real example message | Agents (P2 → `shapes.md` rule), tools, eval cases (the examples verbatim) |
| P3 | **Systems** — what it reads and writes (APIs, DBs, files), and who owns each | Tool list; any write → Q4 HITL |
| P4 | **Out of scope and "good"** — what it must refuse, and how you will know an answer is good | Boundary rules, must-pass evals (Q9) |

## Technology (Q-L, Q1–Q9)

| # | Question | Forks |
|---|----------|-------|
| 1 | **Host** — Node server/container, or Workers/edge? | Node → shape A possible (CopilotRuntime). Edge → shape B (own AG-UI emitter), edge-safe imports only |
| 2 | **Clients** — web React, mobile (headless), chat channel (Slack/Teams), API only? | Web → CopilotKit v2 hooks. Headless → state/custom-event contract. Channel → interrupt as a custom event + card |
| 2v | **Viewports** (web) — smallest supported width, and which of phone (360–430) / tablet (768–1024) / desktop (≥1280)? A design's frame size describes the drawing, not a viewport decision — ask | Breakpoints, the narrow-width state in `/agent-design-ui`, the screenshot widths it checks |
| 3 | **Agent shape** — one agent, a supervisor over several, or a fixed workflow? | `shapes.md` decision rule; count tools per agent |
| 4 | **Writes** — does any tool change data? | Yes → deterministic HITL gate + pending-action ledger + confirm/cancel; one active action per thread |
| 5 | **Identity** — where does verified identity enter, and how do tools read it? | Token verify at the edge → server-injected claims → tools read trusted context; token in request scope only |
| 6 | **Persistence** — checkpoint per thread or per run? Where is the history's source of truth? Long-term memory? | Thread-scoped (durable state) vs run-scoped (history table is truth, checkpoints deleted at run end) |
| 7 | **Models** — providers, fallback order, caller-supplied keys, a cheap model for router/summary/suggestions? | Fallback middleware vs cascade model; key in request scope only |
| 8 | **Observability & privacy** — tracing provider, masking, retention, compliance controls? | Masked-by-default tracing; HMAC user ids |
| 9 | **Evals** — which behaviours are must-pass, which judge model, where does the CI gate sit? | Eval tree separate from unit tests; baseline diff gate |
| D | **Design** — is there a Figma file, mockup or screenshot of the chat? Ask after Q2 | Yes → link recorded in the ADR; after the scaffold, `/agent-design-ui` builds the chat from it. No → stock `CopilotChat` with theme tokens |
| L | **Repo layout** — one app or a monorepo? Ask after Q2 (clients) | `layouts.md`: L1 single app · L2 pnpm + Turborepo. An existing repo's layout is detected, not asked |

## Shape of each question

Ask through `AskUserQuestion` when the tool is available, so the user picks instead of typing:

- `question`: `Q<n> — <one-line question>` plus *why this matters* (what forks downstream) in one sentence.
- 2–4 `options`, the recommended one **first** with `(Recommended)` in its label; each `description` says what that choice changes later (layout, cost, a skill it triggers), citing repo facts. "Other" is added by the tool — never add it yourself.
- Open questions (P1 purpose, P2 example messages) have no fixed options: offer 2–3 drafted answers inferred from the request or the design, and let "Other" carry the user's own words.

Without the tool, write the same as numbered options — `1) <option> (recommended) — <what it changes>` — so a one-character reply works.

One question per call (a design-state batch in `/agent-design-ui` may group up to 4 independent ones). Never put a setup notice, a report or a second topic in the same turn as a question: the answer will be read as answering the wrong thing. A weak answer ("later", "should be fine") gets one hard push, then is recorded as a decision with its stated risk. "Use your recommendation" for the rest → take the recommended option at each remaining question, list them in one message, and record them in the ADR as *defaulted*.

## Output

`docs/adr/0001-agent-architecture.md`:

```markdown
# ADR 0001 — Agent architecture
Status: accepted · Date: <YYYY-MM-DD>

## Problem
Users: · Problem: (P1)
| Task (P2) | Example message | Agent | Tool(s) |
Systems (P3): <system → read/write → owner> · Out of scope (P4): · Good answer means:

## Architecture card
Layout: L1 single app | L2 monorepo · Shape: A | B | hybrid · Host: · Transport: · Clients: · Viewports: <smallest width; phone/tablet/desktop>
Agents: <id → purpose → tool count>
Writes/HITL: · Identity: · Checkpoints: · Memory:
Models: <primary → fallback; router/summary model>
Tracing: <provider, masking> · Evals: <must-pass list, gate>

## Decisions
| # | Decision | Reason | Ladder rung (L0–L3) |

## Rejected alternatives
## Revisit when
```
