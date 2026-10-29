# Architecture interview — question bank

Ordered by blast radius: each answer narrows the ones after it. Skip any question the repo or the user's message already answers — facts are looked up, never asked.

## The problem first (P1–P4) — before any technology

The assistant is built from these answers: every task in P2 must end up owned by an agent and a tool, every system in P3 by a tool, every line of P4 by a boundary rule or an eval.

| # | Question | Becomes |
|---|----------|---------|
| P1 | **Who and why** — who uses it, and what problem does it solve, in one sentence? | Agent purpose, system prompt opening line |
| P2 | **Top tasks** — the 3–5 things users will ask, each with one real example message | Agents (P2 → `shapes.md` rule), tools, eval cases (the examples verbatim) |
| P3 | **Systems** — what it reads and writes (APIs, DBs, files), and who owns each. Does it answer from documents or a knowledge base, and who may read which ones? | Tool list; any write → Q4 HITL; documents → `/agent-rag` (corpus, tenant/ACL key) |
| P4 | **Out of scope and "good"** — what it must refuse, and how you will know an answer is good | Boundary rules, must-pass evals (Q9) |

## Technology (Q-F, Q-L, Q1–Q9)

| # | Question | Forks |
|---|----------|-------|
| F | **Framework**, asked as how the assistant works: *chat that calls a few tools* (LangChain `createAgent`) · *a fixed step-by-step process* (custom LangGraph graph) · *all-in-one TypeScript with workflows and memory built in* (Mastra)? Ask first. Skip it when the request or the repo names the stack | `shapes.md` § Framework: A · M · B/hybrid. Picks the reference row in `reference-repos.md`, and with it the agent tree and which branch every later skill takes |
| 1 | **Host** — Node server/container, or Workers/edge? | Node → shape A possible (CopilotRuntime). Edge → shape B (own AG-UI emitter), edge-safe imports only |
| 2 | **Clients** — web React, mobile (React Native or native), chat channel (Slack/Teams/…), API only? | Web → CopilotKit v2 hooks. React Native → `@copilotkit/react-native`, same hooks. Native or other headless → the AG-UI contract (`${CLAUDE_PLUGIN_ROOT}/rules/agui-transport.md`): shared state, standard interrupt outcome, `resume[]`. Channel → CopilotKit Channels packages + a confirm card (`/agent-hitl` Step 4) |
| 2v | **Viewports** (web) — smallest supported width, and which of phone (360–430) / tablet (768–1024) / desktop (≥1280)? A design's frame size describes the drawing, not a viewport decision — ask | Breakpoints, the narrow-width state in `/agent-design-ui`, the screenshot widths it checks |
| 3 | **Agent shape** — one agent, a supervisor over several, or a fixed workflow? | `shapes.md` decision rule; count tools per agent |
| 4 | **Writes** — does any tool change data? | Yes → deterministic HITL gate + pending-action ledger + confirm/cancel; one active action per thread |
| 5 | **Identity** — where does verified identity enter, and how do tools read it? | Token verify at the edge → server-injected claims → tools read trusted context; token in request scope only |
| 6 | **Persistence** — checkpoint per thread or per run? Where is the history's source of truth? Long-term memory (and recalled by meaning → semantic memory)? Vector store for documents (P3)? | Thread-scoped (durable state) vs run-scoped (history table is truth, checkpoints deleted at run end) |
| 7 | **Models** — providers, fallback order, caller-supplied keys, a cheap model for router/summary/suggestions? | Fallback middleware vs cascade model; key in request scope only |
| 8 | **Observability & privacy** — tracing provider, masking, retention, compliance controls? | Masked-by-default tracing; HMAC user ids |
| 9 | **Evals** — which behaviours are must-pass, which judge model, where does the CI gate sit? | Eval tree separate from unit tests; baseline diff gate |
| D | **Design** — a Figma file, mockup or screenshot of the chat. Never asked: taken from the request or the doc set | Given → link recorded in the ADR; after the scaffold, `/agent-design-ui` builds the chat from it. None → CopilotKit's stock `CopilotChat` with theme tokens, defaulted on the card |
| L | **Repo layout** — one app or a monorepo? Ask after Q2 (clients) | `layouts.md`: L1 single app · L2 pnpm + Turborepo. An existing repo's layout is detected, not asked |
| T | **Test location** — `__tests__/` next to the code, or a separate `tests/` folder outside `src/` mirroring it? Ask after Q-L, only when the repo has no tests yet | Runner `include`/`testMatch`, where every skill writes tests. Existing tests → detect their layout and follow it, never ask |

## Asked or defaulted

Ask only what Claude cannot infer or what is costly to reverse. Everything else is defaulted and confirmed on one card.

| Always asked (one per turn) | Defaulted, shown on the defaults card |
|---|---|
| P1–P4, the problem: nobody but the user knows it | Q1 host, Q2 clients, Q2v viewports, Q-L layout, Q-T test location |
| Q-F framework, only when no stack is named | Q3 agent shape (from P2 by the `shapes.md` rule), Q5 identity (from the auth the repo or stack names) |
| Q4 writes: does any tool change data (it decides the confirm step) | Q-D design (a given link, else stock `CopilotChat`), Q6 memory, Q7 providers and models (primary, fallback, cheap) with a cost line, from `model-choice.md`, Q8 tracing and masking, Q9 must-pass evals (from P2's examples) |

A default comes from, in order: the kickoff doc set, the repo, the request, the recommended option. After the asked questions, show the defaults card: one table (`Question · Default · From`) and one `AskUserQuestion` with *Accept all (Recommended)* / *Change some*. *Change some* → ask only the picked rows, each as its own question. Accepted rows go in the ADR as *defaulted*, with their source. A defaulted Q2v still sets the viewports every later skill shoots at, so it is never dropped, only not asked.

## From the kickoff doc set

When `/kickoff` ran, its files answer these questions. A ✅ row is pre-filled and never asked; a *defaulted* or deferred row is shown on the card and confirmed in one question.

| Doc set | Answers |
|---------|---------|
| `docs/requirements.md` users, problem · top tasks · out of scope, "good" | P1 · P2 · P4 (and Q9 must-pass cases from P2's examples) |
| `docs/requirements.md` § Design · § NFR | Q-D, Q2v · Q8 (privacy, retention, compliance) |
| `docs/stack.md` languages, frameworks, hosting · § Delivery | Q-F, Q1 · Q-L hints (separate deploys) |
| `docs/erd.md` · `docs/api/*` and the ADR's integrations | P3 data the assistant reads or writes · P3 systems, Q4 writes |
| `docs/adr/*` auth and identity · layout | Q5 · Q-L |
| `docs/prerequisites.md` keys and accounts | Step 0 preflight (model key, provider accounts) · Q7 providers |

## Shape of each question

Ask through `AskUserQuestion` when the tool is available, so the user picks instead of typing:

- `question`: `Q<n> — <one-line question>` plus *why this matters* (what forks downstream) in one sentence.
- 2–4 `options`, the recommended one **first** with `(Recommended)` in its label; each `description` says what that choice changes later (layout, cost, a skill it triggers), citing repo facts. "Other" is added by the tool — never add it yourself.
- A label names what the user gets, never a tool: "remembers conversations between visits", not "Postgres + Drizzle". The tech goes in the `description`, in one parenthesis. Ask in tool names only when the user used them.
- Open questions (P1 purpose, P2 example messages) have no fixed options: offer 2–3 drafted answers inferred from the request or the design, and let "Other" carry the user's own words.

Without the tool, write the same as numbered options — `1) <option> (recommended) — <what it changes>` — so a one-character reply works.

One question per call (a design-state batch in `/agent-design-ui` may group up to 4 independent ones). Never put a setup notice, a report or a second topic in the same turn as a question: the answer will be read as answering the wrong thing. A weak answer ("later", "should be fine") gets one hard push, then is recorded as a decision with its stated risk. "Use your recommendation" for the rest → take the recommended option at each remaining question, list them in one message, and record them in the ADR as *defaulted*.

## Output

`docs/adr/<NNNN>-agent-architecture.md` (next free number; it links the kickoff ADR it builds on, if any):

```markdown
# ADR 0001 — Agent architecture
Status: accepted · Date: <YYYY-MM-DD>

## Problem
Users: · Problem: (P1)
| Task (P2) | Example message | Agent | Tool(s) |
Systems (P3): <system → read/write → owner> · Out of scope (P4): · Good answer means:

## Architecture card
Framework: Mastra | LangChain | LangGraph · Reference: <repo>@<sha> · <path>
Layout: L1 single app | L2 monorepo · Tests: `__tests__/` | `tests/` · Shape: A | B | hybrid | M · Host: · Transport: · Clients: · Viewports: <smallest width; phone/tablet/desktop>
Agents: <id → purpose → tool count>
Writes/HITL: · Identity: · Checkpoints: · Memory: · Retrieval: <store, index, embedding model + dims, ACL key | none>
Models: <primary → fallback; router/summary model>
Tracing: <provider, masking> · Evals: <must-pass list, gate>

## Decisions
| # | Decision | Reason | Ladder rung (L0–L3) |

## Rejected alternatives
## Revisit when
```
