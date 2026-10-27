# agent

Skills for building AI assistants on **CopilotKit · AG-UI** with **Mastra, LangChainJS or LangGraph**, each scaffolded from the vendor's official reference repo. Installing it also installs the plugins its skills hand off to:

| Comes with `agent` | For |
|---|---|
| `dev` → `core`, `plan`, `review` | `/project-init` after the scaffold, `/fix-bug` and `/tdd` for red loops, `/verify-done` before saying done, `/review-checklist` and `/blast-radius` on every feature's diff |
| `ship` | `/write-migration` for schema changes, `/finish-branch` to open the PR, `/ci-triage` for a red build |
| `progress` | each skill's checklist and live ✅ progress (hooks only, never blocks) |

Not included: `lead` (retro, skill authoring) and `guards` (commit-blocking hooks — opt in with `/plugin install guards@harness`). The always-loaded rules (`git`, `security`, `code-quality`, `testing`) come only from `bash scripts/install.sh` in a clone; the agent skills carry their own rules in `rules/`.

## Install

```
/plugin marketplace add thanghokdps/claude-root
/plugin install agent@harness
```

Then `/reload-plugins` (or open a new session). Update later with `/plugin marketplace update harness`.

## Start on a blank machine

Open Claude Code in an empty folder and say what you want to build, e.g. *"Tôi muốn làm một chatbot hỗ trợ khách hàng tra cứu đơn hàng"*. `agent-architect` then:

1. **Preflight** — checks git, Node ≥ 20, a package manager, a model key (name only, never the value) and prints the install command for each gap. It installs nothing without asking.
2. **Problem first** — who uses it, the 3–5 tasks with a real example message each, the systems it reads or writes, what it must refuse. One question per turn, each with a recommendation.
3. **Technology** — host, clients, then **single app or monorepo (pnpm + Turborepo)**: you choose; it recommends.
4. **Grill** — every task gets an owner agent and tool, every write a confirm path, every vague answer a recorded risk.
5. **ADR + scaffold** — `docs/adr/<NNNN>-agent-architecture.md`, then the smallest working slice of your layout, ending on one real streamed turn with your first task's example message.

If the designer has a Figma file or mockups, give the link when asked — `agent-design-ui` turns it into the chat UI after the scaffold.

## Grow it, one feature at a time

Ask for a feature in plain words, e.g. *"Thêm tính năng cho khách đổi địa chỉ giao hàng"*. `agent-feature` reads the ADR first and stops if the feature would change the architecture (a new agent, a write path, a system the ADR does not list), lists what already exists, decides **reuse / extend / new** per piece, builds each piece through the layer skill below, then checks the diff for duplicates.

## Skills

| Skill | Reach for it when |
|-------|-------------------|
| `/agent-architect [greenfield\|audit]` | Starting an assistant, or auditing one for custom code that stock middleware now covers |
| `/agent-feature <capability>` | Adding a feature to an existing assistant — within its ADR, reusing what is there, then a duplicate check |
| `/agent-design-ui <figma link \| folder>` | A design for the chat: runs `/design-ui` (dev) for frames, tokens, primitives and the screenshot diff, and adds the chat states, the `[data-copilotkit]` theme and stock vs custom per chat element |
| `/agent-tool <tool>` | Adding, renaming or fixing an agent (backend) tool — schema, trusted identity, read vs mutation, its test. Given your API (OpenAPI, Postman, curl, docs or MCP), it first maps endpoints to tools and builds the typed client and mocks. Browser-only tools go to `/agent-frontend` |
| `/agent-rag <corpus or memory>` | Answering from documents or remembering users by meaning — ingest (chunk, embed, index with model metadata), vector store choice, a retrieval tool with a server-side tenant filter and citations, semantic memory, retrieval evals |
| `/agent-hitl <write>` | A tool creates, updates or deletes data and needs a confirm card — standard AG-UI interrupt, `useInterrupt`, `resume[]` |
| `/agent-graph <scope>` | A request lands on the wrong agent; adding an agent, router or supervisor; defining a fixed workflow; rewriting a system prompt |
| `/agent-frontend <change>` | CopilotKit v2 in React: provider + auth headers, `useAgentContext`, frontend tools (`useFrontendTool`), tool cards (`useRenderTool`), suggestions, file and image attachments, e2e with recorded streams |
| `/agent-verify-turn [local\|prod-trace]` | Before saying an agent change works, or when a production answer was wrong |
| `/agent-evals [unit\|dataset\|suite\|observability\|compare-models]` | Fake-model unit tests; an eval dataset (JSONL, example in `skills/agent-evals/references/dataset-example.jsonl`); judged eval suites with a CI gate; Langfuse/LangSmith tracing with masking; comparing models |
| `/agent-security [scope]` | A new tool, data source or client; before shipping; compliance questions |

Skills fire on their own from what you type — the slash command is optional.

## Demo prompts

1. "Thêm tool cho agent để tra cứu đơn hàng theo mã" → `agent-tool`
2. "Agent xóa user qua chat, cần confirm trước khi lưu" → `agent-hitl`
3. "Hỏi về hóa đơn mà agent support lại trả lời" → `agent-graph`
4. "Sửa rồi mà vẫn bị, chạy thử một turn thật xem stream" → `agent-verify-turn`
5. "Thêm tính năng cho chatbot để khách hủy đơn hàng, dựa trên kiến trúc đã có" → `agent-feature`
6. "Làm UI chat theo design Figma này" → `agent-design-ui`

## Check the routing yourself

`evals/` holds one case per routing demo prompt, one that must not fire, and behaviour cases: `greenfield-problem-first` (prerequisites checked, then the problem asked before any technology), `feature-conflicts-adr` (a feature the ADR rules out is stopped and raised, not built) `design-to-chat` (a frame + tokens mapped onto v2 tokens and a ui-map), `hitl-standard-interrupt` (the stock AG-UI 1.0 confirm path planned, no custom endpoint) and `verify-agui-1` (a captured stream checked against the 1.0 rules). From a clone of the repo:

```bash
bash scripts/eval-plugin.sh agent
```

About $3 for the nine cases. Add `--runs 3 --ablation with-without` for a with/without-plugin comparison. The script targets `plugins/` because each case also loads the dependencies (`progress`, `core`, `plan`, `review`, `dev`, `ship`): a plugin whose dependency is missing is dropped from the run without an error.

## Rules

The invariants the skills read before they act. They load only when a skill needs them, not every session. Building a feature or a tool means following these:

| Rule | Covers | Read by |
|---|---|---|
| [`agent-identity-and-tools.md`](rules/agent-identity-and-tools.md) | identity from trusted context only; **where a tool lives (agent vs frontend)**; read vs mutation, retry, audit, errors, tests | `/agent-tool`, `/agent-feature`, `/agent-frontend`, `/agent-hitl` |
| [`agent-prompts.md`](rules/agent-prompts.md) | system prompts, tool descriptions, scope rules | `/agent-graph`, `/agent-tool` |
| [`agent-stock-first.md`](rules/agent-stock-first.md) | use stock CopilotKit / Mastra / LangChain / LangGraph pieces before custom code | all |
| [`agui-transport.md`](rules/agui-transport.md) | AG-UI 1.0 events, interrupts and resume, untrusted client history, content parts, client contract (0.x lines marked) | `/agent-frontend`, `/agent-hitl` |
| [`langgraph.md`](rules/langgraph.md) | state, run context (`contextSchema`), short- and long-term memory, graph lifecycle, fixed workflows, interrupts | `/agent-graph`, `/agent-hitl` |
| [`mastra.md`](rules/mastra.md) | registry, agents and supervisor, `createTool` + request context, approval/suspend, workflows, storage, transport | `/agent-tool`, `/agent-graph`, `/agent-hitl` |
| [`agent-tracing-privacy.md`](rules/agent-tracing-privacy.md) | tracing switch, masking, what each turn records | `/agent-evals observability`, `/agent-verify-turn` |
| [`agent-deps-pinning.md`](rules/agent-deps-pinning.md) | exact version pins, one copy of the framework core | `/agent-architect` |
| [`agent-code-structure.md`](rules/agent-code-structure.md) what an assistant adds to core's `app-structure.md` (agent folder, CopilotKit theme, recorded streams, evals), tokens instead of raw hex/px, primitives-only gates, mobile-first, Prettier | `/agent-architect`, `/agent-design-ui`, `/agent-feature` |

New feature order (`/agent-feature`): check the ADR → reuse inventory → schema → tool → HITL → agent scope → frontend → evals, one slice green before the next.

## Works alongside

Other plugins with their own agent skills can be installed side by side. When both match a request, name the one you want: `/agent:agent-tool`.
