---
paths:
  - "**/mastra/**/*.{ts,mts}"
---

# Mastra rules (TypeScript)

Checked against mastra.ai docs on 2026-10-23. Confirm each option on the **installed** `@mastra/core` (its `.d.ts`) before relying on it.

## Registry

- One `new Mastra({ agents, tools, workflows, storage, logger, observability })` in `src/index.ts`. Every agent, workflow and shared tool is registered there and nowhere else.
- The key in `agents` is the agent id: it is the client's `agent` prop and the `resourceId` in `registerCopilotKit`. Define it once (`AGENT_ID` in `@repo/shared`; `config/ids.ts` on an L1 repo) and import it in all three places.
- Build the instance once at module level. Never construct `Mastra`, `Agent` or storage per request.
- `mastra dev` serves Studio at `http://localhost:4111`: agents to chat with, workflows rendered as a graph, traces (mastra `docs/src/content/en/docs/studio/overview.mdx`). The closing message shows that URL as the CLI printed it.

## Agents

- `new Agent({ id, description, instructions, model, tools, memory })`. `description` is the scope line a supervisor routes by, so write it like a boundary rule.
- Supervisor: `agents: { … }` on an `Agent`, with per-call `maxSteps`. `.network()` is deprecated, so never start on it.
- Pre-model and post-model behaviour goes in `inputProcessors` / `outputProcessors`, and cross-tool behaviour (audit, timing) goes in `hooks.beforeToolCall` / `afterToolCall`. Their order is a contract, as middleware order is in shape A.
- `model` takes one model or an ordered fallback array of `{ model, maxRetries }` (`ModelWithRetries[]`, @mastra/core 1.81.0 `dist/agent/types.d.ts:452,652`). Use the array for `MODEL_PRIMARY` → `MODEL_FALLBACK`, built by the kit's `models.ts`; the cheap model stays a separate role. A core without the array uses a gateway, decided in the ADR.
- `instructions` as a function receives `{ requestContext }` (`DynamicArgument`, `dist/agent/types.d.ts:569`); 0.x called it `runtimeContext`.

## Tools

- `createTool({ id, description, inputSchema, outputSchema, execute })` with zod. `inputSchema` holds only what the model provides, never `userId`, `tenantId` or `role`.
- Identity comes from `context.requestContext`, set by server middleware after the token is verified. The user goes in `MASTRA_RESOURCE_ID_KEY`, which also scopes memory. Declare `requestContextSchema` on the agent so a missing claim fails the run.
- Tool `id`s are stable: they are in traces, approvals and client renderers.

## Writes (HITL)

- A mutation tool uses `requireApproval: true`, or `suspend()` with `suspendSchema` / `resumeSchema` when the card needs the kit's pending-action fields. Always `return await context.agent.suspend(…)`, because code after it still runs.
- Over AG-UI (`@ag-ui/mastra` ≥ 2): an approval is the standard interrupt with reason `mastra:tool_approval`, approved only by `true` / `{ approved: true }`, declined by `{ approved: false }` or a cancelled resume; any other answer fails the run. At most one interrupt per run.
- A typed reply while the card is open cannot ride `requireApproval` (any payload but the two above fails the run): a card that accepts typed replies is `suspend()` with a `resumeSchema` of `{ approved?: boolean, reply?: string, messageId?: string }`, decided as `${CLAUDE_PLUGIN_ROOT}/skills/agent-hitl/references/card-open-input.md` says; a second `suspend()` asks again when the reply is unclear.
- Both need `storage`. Without it a resume fails with "snapshot not found".
- Code before `suspend()` runs again on resume, so make it idempotent. The real write happens only after the decision.

## Workflows

- A fixed order of steps (validate → then write, prepare → persist → notify) is `createWorkflow` + `createStep` with typed input and output schemas, not a prompt instruction.
- `.commit()` the workflow once at module level and register it in `Mastra`.

## Memory and storage

- Pick storage in the ADR (Q6). Use `LibSQL`/in-memory for dev and a durable store (e.g. `PostgresStore`) where threads must outlive a restart.
- Memory is scoped by the trusted resource id, never by an id the client sends. Recalled memory is untrusted input, like a tool result.

## Transport

- Default (the Dojo, `mastra-ai/ui-dojo`): the runtime is a route on the Mastra server, `server.apiRoutes: [registerCopilotKit({ path, resourceId, identifyUser })]` from `@ag-ui/mastra/copilotkit`, CORS limited to the web origin (never `*`), and `@copilotkit/runtime` kept out of the `mastra build` bundle (`bundler.externals`). The Vite client calls `${VITE_MASTRA_BASE_URL}/<path>`; it never hosts a runtime server of its own.
- The thread sidebar's routes are `registerApiRoute` routes beside it (`chat-threads.md`).
- Only in an existing Next.js repo: in-process, `MastraAgent.getLocalAgents({ mastra })` from `@ag-ui/mastra` behind the Next.js CopilotKit route.
