---
model: opus
effort: high
name: agent-frontend
description: Wires a React web client to an AI agent with CopilotKit v2 — the CopilotKit provider and auth headers, shared agent context, frontend tools, rendering backend tool calls, suggestions, file and image attachments (upload, limits, owner-scoped storage, multimodal parts to the model, retention), and component and e2e tests with recorded AG-UI streams. Use when building or fixing the chat UI of a CopilotKit app, or when tool cards, loading states or headers misbehave in the browser.
when_to_use: CopilotKit provider, useAgent, useAgentContext, useFrontendTool, useRenderTool, useHumanInTheLoop, chat UI bug in React, requests go out unauthenticated, tool card renders twice, loading indicator wrong, suggestions chips, aimock e2e, user attaches a PDF or image in the chat, "gửi ảnh/file cho chatbot", useAttachments, CopilotChat attachments prop
---

# agent-frontend

**Invoke:** `/agent-frontend <the client change or symptom>`

Scope: React web on `@copilotkit/react-core/v2`. How the chat looks — a Figma design, theme, slots — is `/agent-design-ui`; this skill wires it. Mobile/headless clients follow the client contract in `/agent-hitl` and `${CLAUDE_PLUGIN_ROOT}/rules/agui-transport.md`.

---

## Step 1 — Detect

Read the provider, the agent id constant, and the existing tool renderers. Confirm the installed `@copilotkit/*` version and that each hook you plan to use is exported by it (`${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/stock-map.md`).

**Done when:** provider file, agent id source and renderer folder are named, and the version is stated.

## Step 2 — Provider and headers

- Mount CopilotKit only once the auth token is ready.
- The `headers` prop is written to the runtime on mount: pass a value frozen at mount (`useState(() => …)`), never one derived per render.
- Token rotation and optional headers go through **one** effect calling `copilotkit.setHeaders({ ...current, ... })`: spread the current headers, drop optional entries the user cleared, write everything at once. Several effects each spreading a snapshot overwrite each other.
- `agent` prop equals the backend agent id (three-way contract).

**Done when:** a test proves the Authorization header survives mount and is replaced on rotation.

## Step 3 — Context, tools and renderers

- `useAgentContext({ description, value })`: value under a named key, memoised on its inputs — a fresh object each render re-registers forever. Context is display-only, never authorisation.
- Backend tool observed in the UI → `useRenderTool` with the shared tool-name constant; on completion invalidate the affected queries, not patch from the payload; parse the result with a tolerant Zod schema and render a fallback when it does not parse.
- Side effects keyed by `toolCallId` in a ref that lives above the re-created component, so remounts do not re-trigger them.
- Browser-side tools → `useFrontendTool`, registered only for the agent that may call them. Agent or frontend: the table "Where a tool lives" in `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md` decides; data, identity and writes stay in agent tools.
- Clarifying questions may use `useHumanInTheLoop`; mutation confirmations come from the backend gate (`/agent-hitl`).
- Suggestions from the backend endpoint (`useConfigureSuggestions`), never inventing chips for tools that do not exist.
- File or image attachments: follow `${CLAUDE_SKILL_DIR}/references/attachments.md` end to end — `onUpload` to your own route (never base64 inline), server-side type and size checks, owner-scoped storage, one server function building the multimodal parts, extracted text as untrusted data, delete with the thread.

**Done when:** component tests cover each renderer's success, failure and unparsable result, mocking the agent hooks.

## Step 4 — Prove it in the browser

- E2E with recorded streams: `@copilotkit/aimock` (`AGUIMock`) record once against the real agent, replay in CI.
- For a live bug: reproduce in the running app (Playwright MCP or the browser), capture the AG-UI events with `/agent-verify-turn`, and fix the layer that is wrong — backend first if the stream is wrong, client if the stream is right.

**Done when:** the e2e (or the live reproduction) passes on the fixed build, with a screenshot or event log as evidence.
