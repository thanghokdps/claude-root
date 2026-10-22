---
model: opus
effort: high
name: agent-feature
description: Implements a new feature in an existing AI assistant (CopilotKit, AG-UI, LangChainJS, LangGraph) within the architecture its ADR records — checks the feature against the ADR, inventories the tools, agents, schemas, HITL contract and renderers already there, slices the feature across layers with a reuse / extend / new decision per piece, builds each slice through the layer skill, and checks the diff for duplicates. Use when adding a feature or user capability to an assistant that already exists — including one that writes data behind a confirm step, whose write slice this skill hands to agent-hitl.
when_to_use: add a feature to the chatbot, "thêm tính năng cho chatbot", "làm thêm feature cho agent", new capability across tool + UI + confirm, "dựa trên kiến trúc đã có", "đừng viết trùng code", extend the assistant so users can do X
---

# agent-feature

**Invoke:** `/agent-feature <what the user should be able to do>`

A feature built without reading the architecture creates a second way of doing what the repo already does. This skill decides *where* each piece goes and *what it reuses*; the layer skills do the building. Rules: `${CLAUDE_PLUGIN_ROOT}/rules/agent-stock-first.md`, `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md`.

Everything decided here goes in `docs/features/<slug>.md`.

---

## Step 1 — Read the architecture

Read `docs/adr/*` (the agent-architecture ADR first, then later ADRs that amend it) and run the detection in `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/shapes.md`.

- **No ADR** → say so, then either run `/agent-architect audit` to record what exists, or continue with the detected shape as the stated assumption — the user picks.
- **ADR and code disagree** → report both with file paths; never build on the guess.
- Restate the feature as tasks in the ADR's Problem table format (`Task | Example message | Agent | Tool(s)`).

**Done when:** the shape line and the ADR card it rests on are quoted in the feature doc.

## Step 2 — Fit check (stop on conflict)

Check the feature against each line of the card and the ADR's out-of-scope list:

| Conflict | Example |
|----------|---------|
| out of scope (P4) | the ADR excludes payments; the feature takes a payment |
| new agent or new shape | the card has one agent; the feature "needs" a second |
| new write path | the card says read-only, or writes go through HITL and the feature writes directly |
| new system or credential | a system not in P3, a server key where the card says caller credentials |
| new transport, host or client | a mobile client, an edge host |

Any conflict → stop and ask: change the feature, or revisit the architecture with `/agent-architect` and a new ADR. Never widen the architecture inside a feature.

**Done when:** the doc says "fits the ADR", or the user's decision on each conflict is recorded.

## Step 3 — Inventory what exists

Fill the inventory from `${CLAUDE_SKILL_DIR}/references/reuse-inventory.md`: tools and their registry, agents and their scope lines, shared Zod schemas and domain types, the HITL contract and pending-action store, frontend tool renderers and cards, suggestions, eval fixtures. File paths only — no opinions yet.

**Done when:** each inventory row has paths, or "none" with the grep that found nothing.

## Step 4 — Slice and decide

Split the feature into slices per layer and give each one decision:

| Slice | Layer | Decision | Existing piece | Why not reuse (for new) | Built by |
|-------|-------|----------|----------------|-------------------------|----------|
| look up order | tool | **reuse** | `tools/orders/get-order.ts` | — | — |
| cancel order | tool + confirm | **new** | — | no write tool exists for orders | `/agent-tool` → `/agent-hitl` |
| cancel card | frontend | **extend** | `OrderCard` | — | `/agent-frontend` |

- **reuse** when an existing piece already does it; **extend** when a parameter, a field or a variant covers it; **new** only with a reason the two above cannot meet.
- A new piece that resembles an existing one (same upstream, same entity, same card shape) is an *extend* unless the reason says otherwise.
- Layer owners: tool `/agent-tool` · agent scope, routing, prompt `/agent-graph` · write with confirm `/agent-hitl` · client wiring `/agent-frontend` · look from a design `/agent-design-ui` · tests and evals `/agent-evals`.

Show the table and get the user's yes before building.

**Done when:** every slice has a decision, a builder, and each **new** row has its reason.

## Step 5 — Build slice by slice

Run each slice through its layer skill in dependency order (schema → tool → HITL → agent scope → frontend → evals), one slice green before the next. Pass the slice row as the brief so the layer skill does not re-decide placement.

**Done when:** each slice's own Done-when is met, and typecheck, lint and tests pass.

## Step 6 — Duplicate check on the diff

Over the feature's diff, look for what Step 4 should have caught:

- a Zod schema, type or constant that restates one in the inventory → import it;
- two tools on the same upstream endpoint, or a tool description that overlaps another → merge or sharpen the boundary;
- a second renderer, card or confirm mechanism for something that already has one;
- copied helpers (formatting, error mapping, auth headers) → the existing helper.

If `jscpd` is installed, also run `npx jscpd <changed dirs> --min-tokens 50`. Fix each hit or record why it stays.

**Done when:** every hit is fixed or listed in the feature doc with its reason.

## Step 7 — Prove it

Run `/agent-verify-turn` with each example message from Step 1 and one message the feature must not handle. Add the passing turns to the eval suite via `/agent-evals`.

**Done when:** the right agent and tools fire for each example, the out-of-scope message is declined, and the eval cases exist.

---

## Hand-offs

Architecture change → `/agent-architect` · a layer on its own → its skill · security review of a new tool or data source → `/agent-security`.
