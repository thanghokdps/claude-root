---
model: opus
effort: high
name: agent-graph
description: Adds or changes an agent, sub-agent, router, supervisor or fixed workflow in a Mastra, LangGraph or LangChainJS assistant — which agent owns which scope, routing and handoff, boundary rules, workflows with typed steps (Mastra createWorkflow, a fixed LangGraph StateGraph), middleware order, system prompts, and recursion limits. Use when a request lands on the wrong agent, the user asks to add an agent, split scope between agents or define a workflow for the agent, or a system prompt or routing rule needs rewriting.
when_to_use: add an agent, routing, "agent nào làm việc này", supervisor or router node, out-of-scope handling, boundary rules, rewrite the system prompt shorter, wrong agent answered ("hỏi việc này mà agent khác trả lời"), handoff between agents, middleware order, Mastra supervisor agent or workflow, define a workflow for the agent, createWorkflow, createStep, fixed steps validate → approve → write, "tạo workflow cho agent", "quy trình cố định nhiều bước"
---

# agent-graph

**Invoke:** `/agent-graph <the scope or routing change>`

Prompt rules: `${CLAUDE_PLUGIN_ROOT}/rules/agent-prompts.md`. Graph rules: `${CLAUDE_PLUGIN_ROOT}/rules/langgraph.md` (shapes A/B) or `${CLAUDE_PLUGIN_ROOT}/rules/mastra.md` (shape M).

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
- Shape M: routing is a supervisor `Agent` with `agents: { … }`, and each subagent's `description` is its scope line. Never start on `.network()`, which is deprecated.
- **Agent or workflow**: steps that always run in the same order (validate → approve → write, prepare → persist → notify), or steps with no model in them, are a **workflow**, not a prompt instruction and not routing. The model decides *whether* to start it (a tool or the agent's `workflows`); the workflow decides the order.

**Done when:** the owning agent and the layer (router, prompt, tool, middleware) are named.

## Step 3 — Change it

- **Router**: `temperature: 0`, structured output, `nostream`; scope rules as data (ordered rules with a `why`), so order is the contract. Ambiguous → a clarifying question, not a guess. The router text and each agent's description (Mastra subagent `description` included) are generated from one routing profile per agent, never edited apart.
- **Handoff**: bounded (one handoff, then decline) to avoid ping-pong.
- **Decline**: one short line saying what the assistant can do instead.
- **Prompts**: bullets; keep the user's sentences verbatim; derive tool/scope lists from constants; describe only tools that exist.
- **Middleware**: insert at the position the order contract requires (`shapes.md`); reordering changes behaviour even when tests stay green. Shape M's equivalent is the `inputProcessors` / `outputProcessors` order on the agent.
- **Agent id**: a new id changes three places together (`${CLAUDE_PLUGIN_ROOT}/rules/agui-transport.md`).
- **Limits**: recursion limit (shape M: `maxSteps`) and timeout land as a readable turn.
- **Workflow**: shape M → `createWorkflow` + `createStep`, each step with `inputSchema` / `outputSchema` (Zod), `.then()` / `.branch()` / `.parallel()`, `.commit()` once at module level, registered in `new Mastra({ workflows })` (`${CLAUDE_PLUGIN_ROOT}/rules/mastra.md` § Workflows). Shapes A/B → a `StateGraph` with fixed edges and a typed state, compiled once (`${CLAUDE_PLUGIN_ROOT}/rules/langgraph.md` § Fixed workflows). A step that writes waits for a human through the gate `/agent-hitl` owns (`suspend()` / `interrupt()`), with code before it idempotent. The agent reaches the workflow through one tool or the agent's `workflows` map, named in its prompt like any tool; identity comes from the run context, never a step input.

**Done when:** unit tests cover the new routing rule (one prompt per rule plus one out-of-scope), the prompt ↔ tool parity and prompt budget tests (`agent-prompts.md`) pass, each new workflow has a test per step plus one end-to-end run (including the suspended and the declined path when a step waits for a human), and typecheck and lint pass.

## Step 4 — Prove routing

Run the router/routing eval if the repo has one (`/agent-evals`), else `/agent-verify-turn` with an in-scope, a neighbouring-scope and an out-of-scope prompt.

**Done when:** each prompt lands on the expected agent, with the evidence shown. Update the agent/tool map doc if the repo keeps one.
