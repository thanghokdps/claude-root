# DESIGN — harness

How the kit is packaged, what each layer does, and how the AI-assistant skills (`agent`) fit together. To install it, see the README Quickstart. For everyday use, see `docs/USAGE.md`.

---

## 1. Packaging: one marketplace, role plugins, one bundle

From the user's side the kit is **one install**: `harness`. Inside, the skills are grouped into role plugins. That keeps every role's skills in one place, and a teammate who only needs one role can install just that plugin.

```mermaid
graph LR
  kit[harness<br/>bundle]
  kit --> dev & ship & agent & lead & guards
  dev[dev] --> core & plan & review
  ship[ship] --> core
  lead[lead] --> core
  guards[guards<br/>opt-in hooks] --> dev
  agent[agent] --> progress
  core[core] --> progress
  plan[plan] --> progress
  review[review] --> progress
  progress[progress<br/>hooks only]
```

Why role plugins rather than one flat plugin:

| Reason | Effect |
|---|---|
| Every installed skill's description is loaded into every session to route prompts | A frontend dev who installs only `agent` gets 10 skill descriptions instead of about 40, so routing gets fewer misfires |
| Dependencies are declared in `plugin.json` and checked by `scripts/lint-kit.py` | A skill can name another plugin's skill only when that plugin is a dependency, so nothing breaks when a role is installed on its own |
| Each plugin has its own version | A change to `agent` ships without bumping the dev or review skills |
| Hooks are opt-in (`guards`) | Guard rails that block commits never arrive with a plain skill install |

**Naming conventions**

- Plugin: `<role>`, one role per plugin.
- Skill: a verb-noun or noun name that matches its directory, e.g. `fix-bug` or `review-checklist`. AI-assistant skills are named `agent-<layer>`.
- Invocation: `/<skill>`, or `/<plugin>:<skill>` when two plugins define the same name.

## 2. Layers

| Layer | Loaded | Lives in | Holds |
|---|---|---|---|
| Global instructions | every session | `global/CLAUDE.md` → `~/.claude/CLAUDE.md` | principles, lanes, the daily loop |
| Rules | every session (or by `paths:`) | `plugins/core/rules/` → `~/.claude/rules/` | git, security, code quality, typescript, testing |
| Skills | on demand, routed by `description` / `when_to_use` | `plugins/<plugin>/skills/<name>/SKILL.md` | a step-by-step workflow with a "Done when" check |
| References | read by a skill when needed | `plugins/<plugin>/references/`, `skills/<name>/references/` | detail that would bloat the skill |
| Hooks | on events, opt-in | `plugins/guards/hooks/` | risk gate, commit gate, handoff, breadcrumbs |
| Project workspace | per project | `.claude/` written by `/project-init` | project docs, memory, project rules |

Always-loaded context is the budget. Anything that is not needed on every task goes into a skill or a reference.

## 3. Workflow

```mermaid
flowchart TD
  A[git clone the kit anywhere] --> B[bash scripts/install.sh]
  B --> C[cd your-project; claude; /project-init]
  C --> D{prompt}
  D -->|tiny| E[just do it]
  D -->|normal| F[plan mode → build → /verify-done]
  D -->|high-risk| G[specs/slug: SUMMARY, PLAN, TEST_MATRIX → confirm → build → review]
  E & F & G --> H[/review-checklist → /code-review → /finish-branch/]
  H --> I[/compact or /compound at session end/]
```

The Auto-Coordinator in `global/CLAUDE.md` picks the lane. The full routing logic is in `dev:coordinator`.

## 4. AI assistant design (`agent`)

Target stack: TypeScript, **CopilotKit v2** in the web client, **AG-UI** as the transport, and **LangChainJS / LangGraph** on the agent server. Every skill reads its invariants from `plugins/agent/rules/`. These rules load only when a skill reads them, so they cost nothing in other repos.

### Skill per layer

```mermaid
flowchart LR
  arch[/agent-architect<br/>interview → ADR → scaffold/] --> feat[/agent-feature<br/>ADR fit + reuse inventory/]
  feat --> tool[/agent-tool<br/>backend tools/]
  feat --> graph[/agent-graph<br/>agents, routing, prompts/]
  feat --> hitl[/agent-hitl<br/>confirm before write/]
  feat --> fe[/agent-frontend<br/>CopilotKit wiring/]
  fe --> ui[/agent-design-ui<br/>Figma → chat UI/]
  tool & graph & hitl & fe --> verify[/agent-verify-turn<br/>real turn, AG-UI stream/]
  verify --> evals[/agent-evals<br/>dataset, suite, CI gate/]
  evals --> sec[/agent-security<br/>threat model/]
```

### Where each concern lives

| Question | Skill | Rule / reference |
|---|---|---|
| Starting a new assistant: which architecture? | `/agent-architect greenfield` writes an ADR to `docs/adr/` and scaffolds the repo, including `.env.example`, a tracing switch and the first eval cases | `skills/agent-architect/references/shapes.md`, `layouts.md` |
| Adding a feature to an existing assistant | `/agent-feature`: checks the ADR, takes a reuse inventory, and decides reuse / extend / new for each slice | `skills/agent-feature/references/reuse-inventory.md` |
| Defining a backend agent tool | `/agent-tool`: Zod schema, identity from trusted context, read vs mutation, retry and audit | `rules/agent-identity-and-tools.md` |
| Defining a frontend tool, which runs in the browser | `/agent-frontend`: `useFrontendTool`, registered only for the agent allowed to call it | `rules/agent-stock-first.md` |
| Integrating CopilotKit | `/agent-frontend`: provider, auth headers, `useAgent`, `useRenderTool`, and e2e tests against recorded AG-UI streams. `/agent-design-ui` handles the theme and slots | `rules/agui-transport.md` |
| Suggestions | `/agent-frontend`: `useConfigureSuggestions`, served by the backend and limited to tools that exist | — |
| Shared context (page state → agent) | `/agent-frontend`: `useAgentContext`, memoised. It is display-only and never used for authorisation | `/agent-security` covers injection through context |
| Short-term memory (the conversation) | LangGraph checkpointer keyed by `thread_id` | `rules/langgraph.md` § State |
| Long-term memory (across threads) | LangGraph Store, namespaced by the trusted user id | `rules/langgraph.md` § Long-term memory |
| Writes that need user confirmation | `/agent-hitl`: interrupt contract, pending-action record, resume | `rules/langgraph.md` § Interrupts |
| Evaluating prompts, including the dataset | `/agent-evals dataset` → `suite` → `compare-models` | `rules/agent-prompts.md` |
| Observability | Wired by `/agent-architect` at scaffold time; added to an existing repo with `/agent-evals observability`; read with `/agent-verify-turn prod-trace` | `rules/agent-tracing-privacy.md` |
| Proving a change works | `/agent-verify-turn local`: drive a real turn and read the event stream | — |
| Security and compliance | `/agent-security` | `rules/agent-tracing-privacy.md` |

## 5. Quality gates for the kit itself

- `bash scripts/check.sh`: skill lint (frontmatter, dependency check), trigger eval (`eval/triggers/<skill>.json`, 3 prompts per skill must rank it in the top 3), and `claude plugin validate` per plugin.
- `bash scripts/eval-plugin.sh <plugin>`: behaviour evals with a real model. These are paid and not part of `check.sh`.
- Release: bump `version` in each changed `plugin.json`, merge, then run `claude plugin tag plugins/<plugin> --push`.
