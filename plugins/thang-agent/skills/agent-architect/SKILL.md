---
model: opus
effort: high
name: agent-architect
description: Chooses and records the architecture of an AI assistant built on CopilotKit, AG-UI, LangChainJS or LangGraph — a one-question-at-a-time architecture interview for a new assistant, or a stock-versus-custom audit of an existing one — and scaffolds the chosen shape. Use when starting an AI assistant or chatbot project, adding a new assistant product, or asking which agent architecture, createAgent or StateGraph, or whether custom agent code can be replaced by stock middleware.
when_to_use: new AI assistant or chatbot, "chọn kiến trúc agent", "createAgent hay StateGraph", "custom graph hay agent dựng sẵn", scaffold a CopilotKit + LangGraph app, audit an agent repo for custom code that stock now covers, /project-init suggested it
---

# agent-architect

**Invoke:** `/agent-architect [greenfield | audit]`

Picking the wrong shape is the most expensive mistake in an assistant: every later skill builds on it. This skill makes that choice explicit, writes it down, and only then scaffolds.

Rules that apply throughout: `${CLAUDE_PLUGIN_ROOT}/rules/agent-stock-first.md` (the ladder) and `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md` — read both before the first step.

---

## Step 1 — Detect (silent)

Run the detection in `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/shapes.md`. Read `docs/adr/*agent-architecture*` if it exists.

- No agent code yet → **greenfield** (Step 2).
- Agent code exists → **audit** (Step 3).
- An ADR exists and the user did not ask to revisit → report the recorded card and stop.

**Done when:** the `Shape: … · host: … · transport: …` line is written, from grep evidence.

## Step 2 — Greenfield interview

Walk `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/interview.md` in order.

- **One question per turn**, each with *Why this matters* and *My recommendation*. Skip what the repo or the request already answers.
- Default recommendation is shape **A** (createAgent + middleware + CopilotRuntime v2) unless the host is edge/Workers or a contract the runtime cannot express forces **B**; use the decision rule in `shapes.md` for single agent vs supervisor.
- Every non-L0 choice names its rung and its reason (`${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/stock-map.md`).

**Done when:** all nine questions are answered or explicitly deferred with a risk, and the user confirms the architecture card.

Write `docs/adr/0001-agent-architecture.md` from the template in `interview.md`.

## Step 3 — Audit (brownfield)

Follow `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/audit.md`. Report only — no migration in this pass.

**Done when:** every concern in the sweep has a row with a verdict, and every "replace candidate" names its parity test.

Offer to record the keeps and the chosen direction as an ADR.

## Step 4 — Scaffold (greenfield, on request)

Build the smallest working slice of the chosen shape, test first where practical:

1. Env schema that fails at boot on missing or inconsistent config.
2. Identity: verify the token at the edge → server-injected claims → a trusted-context reader for tools; token in request scope only.
3. One agent registered under one agent id (backend registry, `langgraph.json` if used, client `agent` prop).
4. Model factory with fallback; a cheap model for routing/summary.
5. Tracing switch with masking on (`${CLAUDE_PLUGIN_ROOT}/rules/agent-tracing-privacy.md`).
6. Exact pins and a single LangChain copy (`${CLAUDE_PLUGIN_ROOT}/rules/agent-deps-pinning.md`).
7. One read tool through `/agent-tool`, then one real streamed turn through `/agent-verify-turn`.

Apply `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/optimisation.md` as defaults, not as later work: nostream helper nodes, stable prompt prefix, kill switch per tool.

**Done when:** typecheck, lint and tests pass, and one real turn streams end to end with its evidence shown.

---

## Hand-offs

Tools → `/agent-tool` · writes → `/agent-hitl` · more agents or routing → `/agent-graph` · web client → `/agent-frontend` · evals → `/agent-evals` · threat model → `/agent-security`.
