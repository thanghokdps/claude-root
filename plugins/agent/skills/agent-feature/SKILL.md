---
model: opus
effort: high
name: agent-feature
description: Implements a new feature in an existing AI assistant (CopilotKit, AG-UI, Mastra, LangChainJS, LangGraph) within the architecture its ADR records — checks the feature against the ADR, inventories the tools, agents, schemas, HITL contract and renderers already there, slices the feature across layers with a reuse / extend / new decision per piece, builds each slice through the layer skill, and checks the diff for duplicates. Use when adding a feature or user capability to an assistant that already exists — including one that writes data behind a confirm step, whose write slice this skill hands to agent-hitl.
when_to_use: add a feature to the chatbot, "thêm tính năng cho chatbot", "làm thêm feature cho agent", new capability across tool + UI + confirm, "dựa trên kiến trúc đã có", "đừng viết trùng code", extend the assistant so users can do X
---

# agent-feature

**Invoke:** `/agent-feature <what the user should be able to do>`

A feature built without reading the architecture creates a second way of doing what the repo already does. This skill decides *where* each piece goes and *what it reuses*; the layer skills do the building. Rules: `${CLAUDE_PLUGIN_ROOT}/rules/agent-stock-first.md`, `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md`.

Everything decided here goes in `docs/features/<slug>.md`. Started from `/ticket <id>`: its `docs/tickets/<id>/plan.md` is the brief, and the decisions go there instead.

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

Fill the inventory from `${CLAUDE_SKILL_DIR}/references/reuse-inventory.md`: tools and their registry, agents and their scope lines, shared Zod schemas and domain types, the HITL contract and pending-action store, frontend tool renderers and cards, suggestions, retrieval indexes, DB schema and repositories, routes, feature screens and primitives, eval fixtures. File paths only — no opinions yet.

**Done when:** each inventory row has paths, or "none" with the grep that found nothing.

## Step 4 — Slice and decide

Split the feature into slices per layer and give each one decision:

| Slice | Layer | Runs in | Decision | Existing piece | Why not reuse (for new) | Built by |
|-------|-------|---------|----------|----------------|-------------------------|----------|
| look up order | tool | agent | **reuse** | `tools/orders/get-order.ts` | — | — |
| cancel order | tool + confirm | agent (backend interrupt) | **new** | — | no write tool exists for orders | `/agent-tool` → `/agent-hitl` |
| cancel card | frontend | browser (`useInterrupt` card) | **extend** | `OrderCard` | — | `/agent-frontend` |
| `cancelled_at` column | db | server | **new** | — | orders have no cancel state | `/db-change` |
| order history page | screen | browser | **new** | — | no page lists past orders | `/ui-feature` |

- **Runs in** follows `agent-identity-and-tools.md` § Where a tool lives: server data, identity, secrets or audit → agent tool; browser-only effects (navigate, open a panel, fill a form) → frontend tool; fetch-then-show → two tools. A write is always confirmed by the backend interrupt (`/agent-hitl`), never by `useHumanInTheLoop`.
- **reuse** when an existing piece already does it; **extend** when a parameter, a field or a variant covers it; **new** only with a reason the two above cannot meet.
- A new piece that resembles an existing one (same upstream, same entity, same card shape) is an *extend* unless the reason says otherwise.
- Layer owners, agent side: tool `/agent-tool` · agent scope, routing, prompt `/agent-graph` · write with confirm `/agent-hitl` · documents, embeddings, semantic memory `/agent-rag` · chat client wiring `/agent-frontend` · chat look from a design `/agent-design-ui` · tests and evals `/agent-evals`.
- Layer owners, app side (dev): tables, columns, indexes, repository queries `/db-change` · an HTTP route the UI or another client calls `/api-endpoint` · a typed client for the app's own backend or a third-party API `/api-client` · a screen or component outside the chat `/ui-feature` (`/design-ui` when it comes from a design). A slice the chat never touches still goes to its skill; it is never built directly.

Each new or extended piece names its folder per `${CLAUDE_PLUGIN_ROOT}/rules/agent-code-structure.md` (`features/<feature>/`, `components/ui/` only for a second consumer, `server/<aggregate>/`).

Show the table, then ask through `AskUserQuestion`: *build as planned (Recommended)* / *change a slice* / *split into smaller features*. When the user already said "implement all, don't ask", take the recommended option and say so in one line.

**Done when:** every slice has a decision, a builder, and each **new** row has its reason.

## Step 5 — Build slice by slice

Run each slice through its layer skill in dependency order (contract schema → db → API client → endpoint → retrieval → tool → HITL → agent scope → chat frontend → screens → evals), one slice green before the next. Pass the slice row as the brief so the layer skill does not re-decide placement.

- **Invoke the layer skill** (`/agent-tool`, `/agent-hitl`, `/agent-frontend`, `/agent-design-ui`, `/agent-evals`, `/db-change`, `/api-endpoint` …) with the Skill tool for every slice, even a small one. Never build a slice inline from memory of what the skill says: its checks (no identity in the schema, no write before confirm, states, tokens) are what the slice is reviewed against. A slice with no matching skill says so in its row.
- **Code goes to a cheaper model.** Inside the layer skill, the main session decides; the code for the slice goes to one `sonnet` subagent (`model: "sonnet"`) whose brief is the slice row, the contract and the test to make pass, per `model-cost.md` (core). The main session reviews its diff before the next slice.
- **Edit files with Edit or Write**, not shell heredocs, `sed` or scripts, so the repo's edit hooks (lint, format) run on every change.

**Done when:** each slice's own Done-when is met, its layer skill was invoked (or its row says why none fits), and typecheck, lint and tests pass.

## Step 6 — Duplicate check on the diff

Over the feature's diff, look for what Step 4 should have caught:

- a Zod schema, type or constant that restates one in the inventory → import it;
- two tools on the same upstream endpoint, or a tool description that overlaps another → merge or sharpen the boundary;
- a second renderer, card or confirm mechanism for something that already has one;
- copied helpers (formatting, error mapping, auth headers) → the existing helper.

- code shape against `${CLAUDE_PLUGIN_ROOT}/rules/agent-code-structure.md`: files past the size limits, a raw hex or `[Npx]` value in a component, a raw `<button>` / `<input>` / `<textarea>` outside `components/ui/`, an icon size off the scale, a near-copy of a primitive that should be a variant, a dev fixture imported by app code, a third copy of a block.

If `jscpd` is installed, also run `npx jscpd <changed dirs> --min-tokens 50`. Fix each hit or record why it stays.

**Done when:** every hit is fixed or listed in the feature doc with its reason.

## Step 7 — Prove it

Run `/agent-verify-turn` with each example message from Step 1 and one message the feature must not handle; a manual check in the app adds to it and never replaces it. Add the passing turns to the eval suite via `/agent-evals`.

**Done when:** the right agent and tools fire for each example, the out-of-scope message is declined, and the eval cases exist.

## Step 8 — Review and land

A schema change was its own `/db-change` slice in Step 5, and a destructive or long-running one went from there to `/write-migration` (expand/contract, tested down path). Re-check the rows of `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/production.md` the diff touches (kill switch for a new tool, env for the agent server, rollback for a prompt or model change, time limits for a slower tool). A diff that changes a system prompt, a tool description or a structured-output schema goes through `/agent-prompt-review` first. Then `/verify-done` for fresh evidence, `/review-checklist` on the feature's diff (fix what it finds), and `/finish-branch` to open the PR. With several features queued ("implement all"), finish this step for one feature before starting the next.

**Done when:** `/verify-done` shows its evidence, each touched `production.md` row is ✅ or n/a with its reason, and `/review-checklist` has no open must-fix.

---

## Hand-offs

Architecture change → `/agent-architect` · a layer on its own → its skill · security review of a new tool or data source → `/agent-security` · impact of the diff on callers → `/blast-radius` · a failing test or turn → `/fix-bug` · release → `/release-checklist` with `production.md`.
