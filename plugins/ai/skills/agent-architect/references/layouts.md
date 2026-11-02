# Repo layouts — the user picks one (interview Q-L); never assume

Both carry the same rules: one agent id defined once, exact version pins resolved at scaffold time (`<pm> view <pkg> version`, never from memory), `.env` gitignored with a committed `.env.example`.

## L1 — single app (default for one assistant, one web client, one team)

One package, as `mastra-ai/ui-dojo` (R3) does: a Vite SPA and the agent side by side, the CopilotKit runtime a route on the framework's own server.

```
<app>/
  package.json            # dev: concurrently "<mastra dev | langgraph dev>" "vite"
  .env.example            # model key, auth issuer, tracing switch, VITE_*_BASE_URL — names only
  vite.config.ts  index.html
  tsconfig.app.json       # the web code; excludes the agent folder so DOM types never reach it
  tsconfig.node.json      # the agent folder and vite.config.ts
  langgraph.json          # shapes A/B: graphs → ./src/<folder>/<file>.ts:graph · http.app → ./src/<folder>/copilotkit.ts:app
  src/
    main.tsx  App.tsx  pages/  hooks/  lib/  constants.ts      # web: the CopilotKit client only
    components/ui/  components/ai-elements/                    # R3 conventions
    <agent folder>/       # src/mastra/ (M) · src/langchain/ (A) · src/langgraph/ (B), trees below
      ids.ts              # AGENT_ID — the single definition
      env.ts              # zod env schema, fails at boot
      identity.ts         # verify token → trusted context
      models.ts           # model factory + fallback + cheap router model
      tools/<tool>.ts     # one file per tool; its test at the chosen test location (Q-T)
  evals/                  # agent evals, separate from unit tests
```

The web code never holds a server: no `hono`, `@hono/node-server`, `express` or `@copilotkit/runtime` import outside the agent folder.

The rest of the app (features, shared UI, server aggregates, tokens, dev fixtures) is placed by `${CLAUDE_PLUGIN_ROOT}/rules/agent-code-structure.md`.

### The agent tree per framework

The folder is named after the framework and keeps its vendor's files (`reference-repos.md`), with the four kit files beside them:

```
src/mastra/               # shape M (R3)
  index.ts                # the one `new Mastra({ agents, tools, workflows, storage, server: { apiRoutes: [registerCopilotKit(…)] }, … })`
  agents/<name>.ts  tools/<tool>.ts  workflows/<name>.ts

src/langchain/            # shape A (R10)
  agent.ts                # export const graph = createAgent({ … })
  prompts.ts  tools/<tool>.ts
  copilotkit.ts           # Hono app: createCopilotHonoHandler({ runtime, basePath: "/api/copilotkit" })

src/langgraph/            # shape B (R10 on R5)
  graph.ts  state.ts  tools.ts  prompts.ts  configuration.ts
  copilotkit.ts           # as in src/langchain/
```

Only when the user names Next.js: R2 keeps `src/mastra/` and adds `src/agent.ts` (`MastraAgent.getLocalAgents({ mastra })`) behind `src/app/api/copilotkit/route.ts`; R4 puts LangChain/LangGraph in its own `agent/` package beside the Next app.

One dependency list serves both sides, as in the Dojo: `langgraph up`/Docker installs the web deps too (`mastra build` bundles only `src/mastra/`). When the agent and the web must deploy apart, pick L2.

Pick it when: one deployable, no second client planned, Node host.

## L2 — monorepo, pnpm workspaces + Turborepo (default when ≥ 2 clients or agent and web deploy separately)

```
<repo>/
  pnpm-workspace.yaml     # packages: ["apps/*", "packages/*"]
  turbo.json              # build / test / lint / typecheck pipelines
  package.json            # root scripts only, no runtime deps
  .env.example
  apps/
    agent/                # agent server with the CopilotKit runtime as its route: src/mastra/ (registerCopilotKit) or src/langchain|langgraph/ + langgraph.json (http.app), tools, evals/
    web/                  # Vite + CopilotKit client only, R3 conventions (Next.js only when named; add apps/mobile for headless clients)
  packages/
    shared/               # AGENT_ID, interrupt contract types, zod tool schemas shared by server and clients
    config/               # tsconfig + eslint presets
```

Pick it when: web plus mobile or a chat channel, separate deploys, or several agents owned by different people. One copy of the framework core across the workspace (`pnpm why @langchain/core` or `pnpm why @mastra/core` shows one version). Several LangGraph agents → one `apps/<agent>/` each with its own `langgraph.json` (R6).

## Asking

Through `AskUserQuestion` (shape in `interview.md` § Shape of each question):

- question: `Q-L — Repo layout: one app or a monorepo?` — it fixes where the agent id, schemas and interrupt contract live, how clients share them, and the CI pipeline.
- options: `L1 single app` and `L2 pnpm + Turborepo monorepo`, the one that fits Q2 clients and the deploy answer first with `(Recommended)`; each description says what it changes (one deploy vs shared `packages/`, CI shape).

An existing repo's layout is a fact, not a question: detect it (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, workspaces in package.json) and follow it.
