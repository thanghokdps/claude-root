---
paths:
  - "**/mastra/**/*.{ts,mts}"
---

# Mastra rules (TypeScript)

Checked against mastra.ai docs on 2026-10-23. Confirm each option on the **installed** `@mastra/core` (its `.d.ts`) before relying on it.

## Registry

- One `new Mastra({ agents, tools, workflows, storage, logger, observability })` in `src/mastra/index.ts`. Every agent, workflow and shared tool is registered there and nowhere else.
- The key in `agents` is the agent id: it is the client's `agent` prop and the `resourceId` in `registerCopilotKit`. Define it once (`ids.ts`) and import it in all three places.
- Build the instance once at module level. Never construct `Mastra`, `Agent` or storage per request.

## Agents

- `new Agent({ id, description, instructions, model, tools, memory })`. `description` is the scope line a supervisor routes by, so write it like a boundary rule.
- Supervisor: `agents: { … }` on an `Agent`, with per-call `maxSteps`. `.network()` is deprecated, so never start on it.
- Pre-model and post-model behaviour goes in `inputProcessors` / `outputProcessors`, and cross-tool behaviour (audit, timing) goes in `hooks.beforeToolCall` / `afterToolCall`. Their order is a contract, as middleware order is in shape A.
- `model` takes one model, with no fallback array. Fallback and the cheap router model come from the kit's `models.ts` factory or a gateway, decided in the ADR.

## Tools

- `createTool({ id, description, inputSchema, outputSchema, execute })` with zod. `inputSchema` holds only what the model provides, never `userId`, `tenantId` or `role`.
- Identity comes from `context.requestContext`, set by server middleware after the token is verified. The user goes in `MASTRA_RESOURCE_ID_KEY`, which also scopes memory. Declare `requestContextSchema` on the agent so a missing claim fails the run.
- Tool `id`s are stable: they are in traces, approvals and client renderers.

## Writes (HITL)

- A mutation tool uses `requireApproval: true`, or `suspend()` with `suspendSchema` / `resumeSchema` when the card needs the kit's pending-action fields. Always `return await context.agent.suspend(…)`, because code after it still runs.
- Over AG-UI (`@ag-ui/mastra` ≥ 2): an approval is the standard interrupt with reason `mastra:tool_approval`, approved only by `true` / `{ approved: true }`, declined by `{ approved: false }` or a cancelled resume; any other answer fails the run. At most one interrupt per run.
- Both need `storage`. Without it a resume fails with "snapshot not found".
- Code before `suspend()` runs again on resume, so make it idempotent. The real write happens only after the decision.

## Workflows

- A fixed order of steps (validate → then write, prepare → persist → notify) is `createWorkflow` + `createStep` with typed input and output schemas, not a prompt instruction.
- `.commit()` the workflow once at module level and register it in `Mastra`.

## Memory and storage

- Pick storage in the ADR (Q6). Use `LibSQL`/in-memory for dev and a durable store (e.g. `PostgresStore`) where threads must outlive a restart.
- Memory is scoped by the trusted resource id, never by an id the client sends. Recalled memory is untrusted input, like a tool result.

## Transport

- In-process with Next.js: `MastraAgent.getLocalAgents({ mastra })` from `@ag-ui/mastra` behind the CopilotKit route.
- Separate server: `server.apiRoutes: [registerCopilotKit({ path, resourceId })]`, CORS limited to the web origin (never `*`), and `@copilotkit/runtime` kept out of the `mastra build` bundle (`bundler.externals`).
