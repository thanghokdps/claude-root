---
model: opus
effort: high
name: agent-graph
description: Adds or changes an agent, sub-agent, router or supervisor in a LangGraph / LangChainJS assistant — which agent owns which scope, routing and handoff, boundary rules, middleware order, system prompts, and recursion limits. Use when a request lands on the wrong agent, the user asks to add an agent or split scope between agents, or a system prompt or routing rule needs rewriting.
when_to_use: add an agent, routing, "agent nào làm việc này", supervisor or router node, out-of-scope handling, boundary rules, rewrite the system prompt shorter, wrong agent answered, handoff between agents, middleware order
---

# agent-graph

**Invoke:** `/agent-graph <the scope or routing change>`

Prompt rules: `rules/stacks/agent-prompts.md`. Graph rules: `rules/stacks/langgraph.md`.

---

## Step 1 — Detect and map

Run the detection in `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/shapes.md`. Then write the current map:

| Agent id | Scope (one line) | Tools | Not mine → goes to |
|---|---|---|---|

**Done when:** every registered agent and every tool appears in the map, from the code, not from docs.

## Step 2 — Decide where the change belongs

- The feature belongs to the agent whose **scope** it serves, judged from the user's point of view ("viewing my resume" belongs where resume viewing lives, even if a tool elsewhere could answer). State the owner and the reason before editing; if the map leaves two plausible owners, ask.
- Fix behaviour in the agent (routing, prompt, tool) before reaching for a client-side workaround.
- New agent vs bigger agent: use the decision rule in `shapes.md`. Growing past ~10–15 tools or mixing unrelated scopes → split and route.

**Done when:** the owning agent and the layer (router, prompt, tool, middleware) are named.

## Step 3 — Change it

- **Router**: `temperature: 0`, structured output, `nostream`; scope rules as data (ordered rules with a `why`), so order is the contract. Ambiguous → a clarifying question, not a guess.
- **Handoff**: bounded (one handoff, then decline) to avoid ping-pong.
- **Decline**: one short line saying what the assistant can do instead.
- **Prompts**: bullets; keep the user's sentences verbatim; derive tool/scope lists from constants; describe only tools that exist.
- **Middleware**: insert at the position the order contract requires (`shapes.md`); reordering changes behaviour even when tests stay green.
- **Agent id**: a new id changes three places together (`agui-transport.md`).
- **Limits**: recursion limit and timeout land as a readable turn.

**Done when:** unit tests cover the new routing rule (one prompt per rule plus one out-of-scope), and typecheck and lint pass.

## Step 4 — Prove routing

Run the router/routing eval if the repo has one (`/agent-evals`), else `/agent-verify-turn` with an in-scope, a neighbouring-scope and an out-of-scope prompt.

**Done when:** each prompt lands on the expected agent, with the evidence shown. Update the agent/tool map doc if the repo keeps one.
