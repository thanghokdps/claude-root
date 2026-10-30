# agent

Build an AI assistant end to end on **CopilotKit · AG-UI** with **Mastra, LangChainJS or LangGraph**: from one plain-language sentence to an architecture record, a scaffold from the vendor's official reference repo, features built layer by layer, a chat UI from the design, evals and tracing, and a threat model. The product questions come before any technology.

**For:** teams building a chatbot or AI assistant, whether the person asking is a product owner describing it in their own words or an engineer who already chose the stack.

## What it does for you

1. **Start from a sentence.** Open Claude Code in an empty folder and say what the assistant should do, for example *"Tôi muốn làm một chatbot hỗ trợ khách hàng tra cứu đơn hàng"*. `/agent-architect` checks the machine (git, Node ≥ 20, a package manager, a model key by name only), then asks one question per turn with a recommendation: who uses it, the 3–5 tasks with a real example message each, the systems it reads or writes, what it must refuse. Only then host, clients, single app or monorepo. Design is never asked: give a Figma link if you have one.
2. **Get a record and a scaffold.** It writes `docs/adr/<NNNN>-agent-architecture.md`, scaffolds the smallest working slice from the vendor's reference repo at a pinned version (env schema that fails at boot, the caller's identity, one agent, the model factory, a tracing switch with masking on, the stock chat UI), and proves it with one real streamed turn. The secret guard keeps Claude out of `.env`, so your one manual step is `cp .env.example .env` and the model key.
3. **Just the frame?** Say *init* or *dựng* and name the stack without saying what the chatbot does, for example *"init chatbot empty features, dùng Mastra, tracing bằng Langfuse"*. Skeleton mode asks nothing when a stack is named, defaults the rest on one card, and stops at a streamed "hello".
4. **Grow it one feature at a time.** *"Thêm tính năng cho khách đổi địa chỉ giao hàng"* fires `/agent-feature`: it checks the feature against the ADR, inventories what exists, decides reuse / extend / new per piece, builds each piece through the layer skill below, and checks the diff for duplicates.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/agent-architect` | Starting an assistant (`greenfield`), an empty skeleton on a named stack (`skeleton`), or auditing an existing one for custom code that stock pieces now cover (`audit`). Also when choosing Mastra vs `createAgent` vs `StateGraph` | "build a chatbot for our support team" · "Mastra hay LangChain?" |
| `/agent-feature` | Adding a capability to an assistant that already exists, within its ADR. A write behind a confirm step starts here and is handed to `/agent-hitl` | "thêm tính năng cho chatbot để khách hủy đơn hàng" |
| `/agent-tool` | Adding, renaming or fixing a backend agent tool: Zod schema, identity from trusted context, read vs mutation, retry and audit, its test. Given your API (OpenAPI, Postman, curl, docs or an MCP server) it maps endpoints to tools and builds the typed client and mocks | "thêm tool cho agent tra cứu đơn hàng theo mã" · "tạo tools từ swagger này" |
| `/agent-hitl` | A tool creates, updates or deletes data and needs a confirm card: the standard AG-UI interrupt and resume, a pending-action record, confirm / cancel / replay, the right target record | "agent xóa user qua chat, cần confirm trước khi lưu" |
| `/agent-graph` | A request lands on the wrong agent, you add an agent, router or supervisor, define a fixed workflow, or rewrite a system prompt | "hỏi về hóa đơn mà agent support lại trả lời" |
| `/agent-frontend` | CopilotKit v2 in React: provider and auth headers, shared context, frontend tools, rendering tool calls, suggestions, file and image attachments, e2e tests on recorded AG-UI streams | "tool card renders twice" · "gửi ảnh cho chatbot" |
| `/agent-design-ui` | The design is for the chat itself: chat states, the `[data-copilotkit]` theme, stock slot vs custom component per element. Extends `/design-ui` | "làm UI chat theo design Figma này" |
| `/agent-rag` | The assistant must answer from documents or remember users by meaning: ingest pipeline, vector store, a retrieval tool with a server-side tenant filter and citations, semantic recall, retrieval evals | "chatbot trả lời từ tài liệu nội bộ" |
| `/agent-evals` | Adding tests, an eval dataset or tracing to an agent, or choosing a model: `unit` (fake models), `dataset` (JSONL), `suite` (judged, with a baseline gate for CI), `observability` (Langfuse / LangSmith with masking), `compare-models` | "test agent không cần gọi model thật" · "switch to a cheaper model" |
| `/agent-verify-turn` | Before saying an agent change works (`local`: drive a real turn and read the event stream), or when a production answer was wrong (`prod-trace`: find the trace and classify the cause first) | "sửa rồi mà vẫn bị, chạy thử một turn thật" |
| `/agent-security` | A new tool, data source or client; before shipping; a compliance question. Injection through tool results, context and memory; confused deputy; exfiltration through rendered output; PII in traces; SOC 2 mapping | "client gửi cả lịch sử chat, có an toàn không?" |
| `/agent-prompt-review` | A diff touches a system prompt, tool description or output schema. Read as the model reads it: injection openings, promised capabilities that do not exist, ambiguity, fragile formats, token waste, with an eval per must-fix | "soát prompt trước khi mở PR" |

Skills fire on their own from what you type; the slash command is optional. When another installed plugin has a skill of the same name, name this one: `/agent:agent-tool`.

## Rules the skills follow

They load only when a skill reads them, so they cost nothing in other repos.

| Rule | Covers | Read by |
|---|---|---|
| [`agent-identity-and-tools.md`](rules/agent-identity-and-tools.md) | identity from trusted context only; where a tool lives (agent vs frontend); read vs mutation, retry, audit, errors, tests | `/agent-tool`, `/agent-feature`, `/agent-frontend`, `/agent-hitl` |
| [`agent-prompts.md`](rules/agent-prompts.md) | system prompts, tool descriptions, scope rules | `/agent-graph`, `/agent-tool`, `/agent-prompt-review` |
| [`agent-stock-first.md`](rules/agent-stock-first.md) | stock CopilotKit / Mastra / LangChain / LangGraph pieces before custom code | all |
| [`agui-transport.md`](rules/agui-transport.md) | AG-UI events, interrupts and resume, untrusted client history, content parts, client contract | `/agent-frontend`, `/agent-hitl` |
| [`langgraph.md`](rules/langgraph.md) | state, run context, short- and long-term memory, graph lifecycle, fixed workflows, interrupts | `/agent-graph`, `/agent-hitl` |
| [`mastra.md`](rules/mastra.md) | registry, agents and supervisor, `createTool` with request context, approval and suspend, workflows, storage, transport | `/agent-tool`, `/agent-graph`, `/agent-hitl` |
| [`agent-tracing-privacy.md`](rules/agent-tracing-privacy.md) | the tracing switch, masking, what each turn records | `/agent-evals observability`, `/agent-verify-turn`, `/agent-security` |
| [`agent-deps-pinning.md`](rules/agent-deps-pinning.md) | exact version pins, one copy of the framework core | `/agent-architect` |
| [`agent-code-structure.md`](rules/agent-code-structure.md) | what an assistant adds to the app structure (agent folder, theme, recorded streams, evals), tokens instead of raw values, mobile-first | `/agent-architect`, `/agent-design-ui`, `/agent-feature` |

## Hooks

None of its own. The always-on gates come from `core` and `dev` (secret guard, branch guard, ticket gate, test lock).

## Depends on

`progress`, `dev`, `ship`, and through them `core`, `plan`, `review`. That is the build loop the agent skills hand off to: `/project-init` after the scaffold, `/fix-bug` and `/tdd` for red loops, `/verify-done` before saying done, `/review-checklist` and `/blast-radius` on every feature's diff, `/write-migration` for schema changes, `/finish-branch` to open the PR. Not included: `lead` and the opt-in `guards`.

## Check the routing yourself

`evals/` holds one case per demo prompt plus behaviour cases, for example `greenfield-problem-first` (the problem is asked before any technology), `skeleton-no-questions` (a named stack asks nothing and builds), `feature-conflicts-adr` (a feature the ADR rules out is raised, not built), `hitl-standard-interrupt`, `rag-tenant-filter` and `security-forged-history`. From a clone of the kit, with a real model (paid):

```bash
bash scripts/eval-plugin.sh agent
```

Add `--runs 3 --ablation with-without` for a with/without-plugin comparison.

## Install

```text
/plugin install agent@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). In an AI-assistant repo, core's `repo-profile` hook enables this plugin on its own. Optional MCP servers the skills use when present: Playwright (`claude mcp add playwright -- npx -y @playwright/mcp@latest`) to render the chat in a real browser, Figma for `/agent-design-ui`. All plugins: [`../README.md`](../README.md).
