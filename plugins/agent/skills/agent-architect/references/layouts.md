# Repo layouts — the user picks one (interview Q-L); never assume

Both carry the same rules: one agent id defined once, exact version pins resolved at scaffold time (`<pm> view <pkg> version`, never from memory), `.env` gitignored with a committed `.env.example`.

## L1 — single app (default for one assistant, one web client, one team)

```
<app>/
  package.json            # one app: Next.js + CopilotKit runtime route + agent code
  .env.example            # model key, auth issuer, tracing switch — names only
  src/
    app/api/copilotkit/route.ts   # CopilotRuntime endpoint (shape A) or AG-UI emitter (shape B)
    app/page.tsx                  # <CopilotKit runtimeUrl agent=AGENT_ID>
    agent/
      ids.ts              # AGENT_ID — the single definition
      env.ts              # zod env schema, fails at boot
      identity.ts         # verify token → trusted context
      models.ts           # model factory + fallback + cheap router model
      agents/<name>.ts    # createAgent / StateGraph
      tools/<tool>.ts     # one file per tool + <tool>.test.ts
  evals/                  # agent evals, separate from unit tests
```

Pick it when: one deployable, no second client planned, Node host.

## L2 — monorepo, pnpm workspaces + Turborepo (default when ≥ 2 clients or agent and web deploy separately)

```
<repo>/
  pnpm-workspace.yaml     # packages: ["apps/*", "packages/*"]
  turbo.json              # build / test / lint / typecheck pipelines
  package.json            # root scripts only, no runtime deps
  .env.example
  apps/
    agent/                # agent server: createAgent/StateGraph, CopilotRuntime or AG-UI endpoint, tools, evals/
    web/                  # Next.js + CopilotKit client (add apps/mobile for headless clients)
  packages/
    shared/               # AGENT_ID, interrupt contract types, zod tool schemas shared by server and clients
    config/               # tsconfig + eslint presets
```

Pick it when: web plus mobile or a chat channel, separate deploys, or several agents owned by different people. One LangChain copy across the workspace (`pnpm why @langchain/core` shows one version).

## Asking

```
**Q-L — Repo layout: one app (L1) or a monorepo (L2)?**

Why this matters: it fixes where the agent id, schemas and interrupt contract live, how clients share them, and the CI pipeline.

My recommendation: <L1 or L2> — <reason from Q2 clients and the deploy answer>.
```

An existing repo's layout is a fact, not a question: detect it (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, workspaces in package.json) and follow it.
