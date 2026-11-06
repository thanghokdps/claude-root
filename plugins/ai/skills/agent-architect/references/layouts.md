# Repo layouts — monorepo by default

Both layouts carry the same rules: one agent id defined once, exact version pins resolved at scaffold time (`<pm> view <pkg> version`, never from memory), `.env` gitignored with a committed `.env.example`.

**Paths in the kit.** `<agent app>` is `apps/agent` on L2 and the repo root on L1; `<web app>` is `apps/web` on L2 and the repo root on L1. A path such as `src/mastra/index.ts` or `evals/run.ts` in a rule or skill is read from `<agent app>`; `src/components/` and `src/styles/` from `<web app>`.

## L2 — monorepo, pnpm workspaces + Turborepo (default)

The web and the agent are separate packages, so each has its own dependencies, build and deploy, and the web cannot reach the agent's code.

```
<repo>/
  pnpm-workspace.yaml     # packages: ["apps/*", "packages/*"]; onlyBuiltDependencies
  turbo.json              # build / dev / test / lint / typecheck, with "envMode": "loose"
  package.json            # root scripts only, no runtime deps; names packageManager exactly
  .env.example            # model key, INTERNAL_API_TOKEN, auth issuer, tracing switch and keys, VITE_*_BASE_URL — secrets empty, a comment above each saying where it comes from
  apps/
    agent/                # package "agent": the agent server with the CopilotKit runtime as its route
      package.json  tsconfig.json  tsup.config.ts    # tsup.config.ts on A/B only
      src/<agent folder>/  # src/mastra/ (M) · src/langchain/ (A) · src/langgraph/ (B): the trees below
      src/server/<system>/ # external API clients (rules/agent-code-structure.md)
      evals/              # agent evals, separate from unit tests
      scripts/            # graph.ts on A/B
    web/                  # package "web": Vite + the CopilotKit client only
      package.json  tsconfig.json  vite.config.ts  index.html
      src/
        main.tsx  App.tsx  pages/  hooks/  lib/  constants.ts
        components/ui/  components/ai-elements/              # R3 conventions
      e2e/                # Playwright specs
  packages/
    shared/               # package "@repo/shared": AGENT_ID, interrupt contract types, zod tool schemas shared by the agent and its clients
    config/               # package "@repo/config": tsconfig + eslint presets
```

- **Shared code.** `@repo/shared` ships TypeScript source with no build step: `"exports": { ".": "./src/index.ts" }`, as the company's `packages/shared` does. Both apps depend on it with `workspace:*`. `AGENT_ID` lives here, not in `config/ids.ts`. A type or schema moves here once both apps need it, not before. A new package under `packages/` needs code that already has two consumers.
- **Boundary.** `apps/web/package.json` lists no `@repo` package except `shared` and `config`, and no framework or server package (`hono`, `@hono/node-server`, `express`, `@copilotkit/runtime`, `@langchain/*`, `@mastra/*`). `apps/agent` is never a dependency of anything. pnpm's strict `node_modules` then makes a stray import fail to resolve.
- **One framework core.** `pnpm why @langchain/core` or `pnpm why @mastra/core` shows one version. `zod` is one version across the workspace.
- **`.env` lives at the root**, so `setup-env.sh` and the preflight stay one command. The apps reach it explicitly: `tsx --env-file=../../.env` on A/B, `mastra dev --env ../../.env` on M (mastra 1.38.0 `dev --help`), and `envDir: "../.."` in `vite.config.ts` (vite 8.3.6 `dist/node/index.d.ts:3508-3512`; only `VITE_*` reaches the bundle).
- **Turbo env mode.** `"envMode": "loose"` at the top of `turbo.json`. In the default strict mode a shell variable never reaches a task: `SPIKE_PORT=1234 turbo run probe` printed `undefined` on turbo 2.11.10, and `PORT=… pnpm dev` or `TOOL_CURRENT_TIME=off pnpm dev` would be ignored without a word.

Root scripts:

```json
{
  "scripts": {
    "dev": "turbo run dev",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "typecheck": "turbo run typecheck",
    "format:check": "prettier --check ."
  }
}
```

`turbo.json`:

```json
{
  "$schema": "https://turbo.build/schema.json",
  "envMode": "loose",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", "dist-server/**", ".mastra/output/**"]
    },
    "dev": { "cache": false, "persistent": true },
    "test": {},
    "lint": {},
    "typecheck": {}
  }
}
```

`apps/agent/package.json` scripts: `embed-server.md` § `package.json` on A/B; `"dev": "mastra dev --env ../../.env"`, `"build": "mastra build"`, `"start": "mastra start"` on M. `mastra build` bundles a TypeScript-source workspace package into `.mastra/output` on its own, with no `@repo/shared` left in the output (mastra 1.38.0, built and booted on 2026-11-06). `apps/web/package.json`: `"dev": "vite"`, `"build": "vite build"`.

Several LangGraph agents → one `apps/<agent>/` each (R6). A mobile app or a chat channel → `apps/mobile` or `apps/<channel>`, sharing `@repo/shared`.

## The app inside each package

The web code never holds a server: no `hono`, `@hono/node-server`, `express` or `@copilotkit/runtime` import outside the agent folder.

The rest of the app (features, shared UI, server aggregates, tokens, dev fixtures) is placed by `${CLAUDE_PLUGIN_ROOT}/rules/agent-code-structure.md`.

### The agent tree per framework

The folder is named after the framework. Its root holds only the vendor's own files, as the reference repo lays them out (`reference-repos.md`), plus `prompts.ts`. Every file the kit adds goes in a folder per concern, with the same names in all three shapes:

```
config/          env.ts (zod env schema, fails at boot) · ids.ts (AGENT_ID, the single definition, on L1 only) · models.ts (primary + fallback + cheap roles)
auth/            identity.ts (verify token → trusted context reader)
guardrails/      pii.ts (A/B). Shape M calls this folder processors/, Mastra's term for input/output processors
observability/   tracing.ts (the TRACING_PROVIDER switch, masking on)
server/          A/B only: main.ts (the one process), agent-api.ts (the guarded embed server), persistence.ts, copilotkit.ts (the `createCopilotHonoHandler` app) and its helpers (route builder, stream filter)
```

A new kit file joins the group it belongs to. A new concern gets its own folder, never a loose file at the root. Mastra is unopinionated beyond its own folders, but the docs ask for a structure kept consistent (mastra.ai/docs/getting-started/project-structure). LangGraph's application-structure example keeps only the graph entry at `src/` and moves the rest one folder down (docs.langchain.com/oss/javascript/langgraph/application-structure).

```
src/mastra/               # shape M (R3)
  index.ts                # the one `new Mastra({ agents, tools, workflows, storage, server: { apiRoutes: [registerCopilotKit(…)] }, … })`
  agents/<name>.ts  tools/<tool>.ts  workflows/<name>.ts      # vendor folders; scorers/ and mcp/ when used
  routes/threads.ts       # the thread sidebar's registerApiRoute routes (rules/chat-threads.md)
  prompts.ts
  config/  auth/  processors/  observability/

src/langchain/            # shape A (R10)
  agent.ts                # export const graph = createAgent({ … })
  prompts.ts  tools/<tool>.ts
  config/  auth/  guardrails/  observability/
  server/main.ts  agent-api.ts  persistence.ts    # the embed server (references/embed-server.md)
  server/copilotkit.ts    # export const app = createCopilotHonoHandler({ runtime, basePath: "/api/copilotkit", cors, hooks })
  server/threads.ts       # the thread sidebar's routes, answered in hooks.onRequest (rules/chat-threads.md)

src/langgraph/            # shape B (R10 on R5)
  graph.ts  state.ts  tools.ts  prompts.ts  configuration.ts
  config/  auth/  guardrails/  observability/
  server/copilotkit.ts  server/threads.ts    # as in src/langchain/
```

Tests follow the groups. With `__tests__/` (Q-T), a group's unit tests sit in its own `__tests__/` (`config/__tests__/env.test.ts`, `guardrails/__tests__/pii.test.ts`). Tests that span groups stay in `src/<agent folder>/__tests__/`: the prompt tests, the deprecated-import lint test and its `fixtures/`, and the shared `helpers/` and fakes. With `tests/`, the same groups are mirrored under it.

Only in an existing Next.js repo: R2 keeps `src/mastra/` and adds `src/agent.ts` (`MastraAgent.getLocalAgents({ mastra })`) behind `src/app/api/copilotkit/route.ts`; R4 puts LangChain/LangGraph in its own `agent/` package beside the Next app.

## L1 — single app (only when asked)

One package, as `mastra-ai/ui-dojo` (R3) does: a Vite SPA and the agent side by side, the CopilotKit runtime a route on the framework's own server.

```
<app>/
  package.json            # dev: concurrently "<mastra dev | tsx watch src/<folder>/server/main.ts>" "vite"
  .env.example
  vite.config.ts  index.html
  tsconfig.app.json       # the web code; excludes the agent folder so DOM types never reach it
  tsconfig.node.json      # the agent folder and vite.config.ts
  src/
    main.tsx  App.tsx  pages/  hooks/  lib/  constants.ts      # web: the CopilotKit client only
    components/ui/  components/ai-elements/                    # R3 conventions
    <agent folder>/
  evals/                  # agent evals, separate from unit tests
```

One dependency list serves both sides, as in the Dojo: `langgraph up`/Docker installs the web deps too (`mastra build` bundles only `src/mastra/`). The web and the agent can still run as two services, but they share one dependency list, one pipeline and no enforced boundary.

Pick it when: the user asks for one app or one package. Never as the default, because a growing team ends up splitting it.

## Choosing

- **New repo:** L2, shown on the defaults card as `Q-L layout`. L1 only when the request says one app, one package or no monorepo.
- **Existing repo:** its layout is a fact, not a question: detect it (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, workspaces in package.json) and follow it. An existing L1 repo stays L1; moving it to L2 is a change the user asks for.
- The question, when the card's row is challenged, goes through `AskUserQuestion` (shape in `interview.md` § Shape of each question): `Q-L — Repo layout: monorepo or one app?`, with `L2 pnpm + Turborepo monorepo (Recommended)` first and `L1 single app` second; each description says what it changes (shared `packages/` and per-app deploys vs one package).
