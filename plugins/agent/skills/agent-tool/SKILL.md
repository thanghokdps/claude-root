---
model: opus
effort: high
name: agent-tool
description: Adds or changes an LLM agent tool (Mastra createTool, LangChain tool()) in a Mastra, LangChainJS or LangGraph assistant — Zod schema, trusted-context identity, read versus mutation, retry and audit wrappers, short tool description, and its test. Also turns an API the user provides (OpenAPI/Swagger spec, Postman collection, curl commands, API docs, or an MCP server) into a confirmed endpoint-to-tool map, a typed client and spec-based mocks. Use when the user asks to add, remove, rename or fix an agent tool, change what a tool returns, tighten a tool description, or build tools from their API.
when_to_use: add a tool, "thêm tool cho agent", "chỉ giữ 2 tool này", tool description or scope wording, tool returns wrong data, tool schema, DynamicStructuredTool or tool() from @langchain/core, createTool from @mastra/core, "đây là API của tôi", "tạo tools từ swagger/OpenAPI/Postman", implement tools with my API, connect an MCP server's tools to the agent
---

# agent-tool

**Invoke:** `/agent-tool <what the tool should do>`

The invariants live in `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md`; this skill is the order of work.

---

## Step 0 — From an API the user provides (when there is one)

The user handed over an API (spec, collection, curl, docs page or MCP server) rather than one tool → follow `${CLAUDE_SKILL_DIR}/references/api-to-tools.md` first: one spec in `docs/api/`, the endpoint → tool table confirmed by the user, then one client per system in `server/<system>/` with generated types, error mapping, trimming and spec-based mocks. An MCP server is connected, never rewrapped.

Then run Steps 1–4 below **once per tool**, read tools first. Write tools also go through `/agent-hitl`.

**Done when:** every endpoint has a decision in `docs/api/<system>.tools.md`, the user has confirmed it, and the client typechecks against the generated types.

## Step 1 — Detect and place

First decide agent tool or frontend tool with "Where a tool lives" in `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md`; a browser-only tool goes to `/agent-frontend` instead.

Run the detection in `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/shapes.md`, then find where tools of this kind already live (the tool registry, the domain slice, the agent that owns the scope).

- Shape A: schema-only tool + execution in the agent's `wrapToolCall` middleware, or a real handler — follow what the agent already does.
- Shape B: a real handler reading `config.configurable`, registered in the domain registry as `read` or `mutation`.
- Shape M: `createTool({ id, description, inputSchema, outputSchema, execute })` in `src/mastra/tools/`, attached to the owning `Agent`'s `tools`. `execute(input, context)` reads identity from `context.requestContext` (server-set, `MASTRA_RESOURCE_ID_KEY` for the user), never from `input`. Rules: `${CLAUDE_PLUGIN_ROOT}/rules/mastra.md`.
- The tool belongs to the agent whose scope it serves. If two agents could own it, ask which — that is a decision, not a fact.

**Done when:** the owning agent, the registry entry, and read-vs-mutation are stated with file paths.

## Step 2 — Contract first

1. Name and description as constants. Description in short bullets: when to use, what it returns, what it cannot do. If the user supplied wording, keep it verbatim.
2. Zod schema with only what the model must provide. No identity or authority fields (`userId`, `actingAs`, `tenantId`, `role`).
3. Output: a compact, typed result the model can quote — not a raw upstream payload.

**Done when:** a failing test exists for: schema rejects identity fields · happy path · upstream error becomes a short user-facing message.

## Step 3 — Implement

- Identity and authority from trusted context only; the upstream call uses the caller's credentials or a server credential scoped by those claims.
- Read tool: wrap with retry (stock `toolRetryMiddleware` scoped to read tools when available; shape M retries inside `execute`, read tools only — `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/stock-map.md`), audit outside retry.
- Mutation tool: stop here and run `/agent-hitl` — a mutation is never a plain tool.
- Missing required input → ask the user for it (end the turn), never guess.
- A tool that reads a user's attachment takes the attachment id, loads it with the owner check, and returns its extracted text as delimited data, never as instructions (`${CLAUDE_PLUGIN_ROOT}/skills/agent-frontend/references/attachments.md` §3, §5).
- Removing a tool: remove it from the registry, prompts, suggestions, client renderers and docs in the same change.

**Done when:** the Step 2 tests pass, plus typecheck and lint.

## Step 4 — Prove it in a turn

Run `/agent-verify-turn` with a prompt that should pick this tool and one that should not. Paste the tool-call events as evidence.

**Done when:** the right tool is called with the expected args, and the wrong-scope prompt does not call it.
