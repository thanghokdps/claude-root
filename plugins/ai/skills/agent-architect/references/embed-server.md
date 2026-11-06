# Embed server — shapes A and B on one Node process

Read with `skeleton.md` § 4 and `rules/langgraph.md` § Transport. Shapes A and B serve the graph, the CopilotKit runtime and the thread routes from one Node process that the team owns. Shape M has its own server (`mastra build`) and skips this file.

Run live on 2026-11-05 on Node 24 with a fake streaming OpenAI server, against @langchain/langgraph-api 1.5.8, @copilotkit/runtime 1.84.1, hono 4.13.5, @hono/node-server 2.1.3 and better-sqlite3 12.11.1, on SQLite, Postgres 17 and D1 through a local Worker: streamed turn, thread list, history and context after a process restart, a tool call, Stop, a second caller, and a Docker image running as non-root. Shape B ran the same turn, tool, restart and auth checks. In a browser, on shape A with a slow fake model, Stop ended the model call, the words stayed on screen, and the next turn's model request held them, stored by `keepStoppedAnswer` of `rules/chat-threads.md` through the guarded API.

## Why this server

`langgraphjs dev` is an in-memory dev server. Its production image (`langgraphjs build`) needs `LANGGRAPH_CLOUD_LICENSE_KEY`, and the pricing page lists self-hosting as Enterprise. `createEmbedServer` from `@langchain/langgraph-api/experimental/embed` is MIT and serves the same thread and run routes from a Hono app, so dev and production run the same code. It is marked experimental and does not follow semver: pin it exactly, and re-run § Tests before moving the pin.

## What the embed server does not do

Each row was read in `@langchain/langgraph-api` 1.5.8 `dist/experimental/embed/`, and `agent-api.ts` below closes it:

| Gap                                                                                | Closed by                                                               |
| ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| No auth. It trusts every request                                                   | The guard checks `INTERNAL_API_TOKEN` and the caller headers            |
| No `/assistants` routes, which the adapter reads                                   | `assistantRoutes`                                                       |
| Run config comes only from the request body                                        | `withVerifiedCaller` writes `config.configurable.langgraph_auth_user`   |
| `POST /threads` and search have no owner scope                                     | The guard stamps `metadata.owner` and forces it into the search         |
| The state route reads `thread.metadata.graph_id`                                   | The guard stamps `graph_id` when a thread is created                    |
| `runs/:id/cancel` drops queued runs only, so Stop leaves the model running         | `activeRuns` aborts the run's signal (`runs.mjs:116-127`)               |
| The stateless `/runs/*` routes have no thread, so no owner                         | The guard answers 404 to anything outside `/threads` and `/assistants`  |
| A graph factory is never called, so a per-turn trace handler has nowhere to attach | `streamEvents` is overridden on a copy of the graph (§ `agent.ts` tail) |

## `server/agent-api.ts`

```ts
import { createEmbedServer } from "@langchain/langgraph-api/experimental/embed";
import type { ThreadSaver } from "@langchain/langgraph-api/experimental/embed";
import type { BaseCheckpointSaver } from "@langchain/langgraph";
import { Hono } from "hono";
import { callerFromHeaders, sameSecret } from "../auth/identity";
import type { Caller } from "../auth/identity";
import { AGENT_ID } from "@repo/shared";

type EmbedOptions = Parameters<typeof createEmbedServer>[0];
type RunBody = {
  metadata?: Record<string, unknown>;
  config?: { configurable?: Record<string, unknown> };
};

const THREAD_PATH = /^\/threads\/([^/]+)(\/.*)?$/;
const THREAD_RUN_PATH = /^\/threads\/[^/]+\/runs(\/stream)?$/;
const RUN_CANCEL_PATH = /^\/threads\/[^/]+\/runs\/[^/]+\/cancel$/;

/** The embed server takes identity only from the run body, so the guard writes it there. */
function withVerifiedCaller(body: RunBody, caller: Caller): RunBody {
  return {
    ...body,
    metadata: { ...body.metadata, owner: caller.id },
    config: {
      ...body.config,
      configurable: {
        ...body.config?.configurable,
        langgraph_auth_user: {
          identity: caller.id,
          display_name: caller.name,
          time_zone: caller.timeZone,
        },
      },
    },
  };
}

// The adapter reads these; the embed server registers no /assistants routes.
function assistantRoutes(graphs: EmbedOptions["graph"]) {
  const routes = new Hono();
  const row = (id: string) => ({
    assistant_id: id,
    graph_id: id,
    name: id,
    config: {},
    metadata: {},
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    version: 1,
  });
  routes.post("/assistants/search", (c) =>
    c.json(Object.keys(graphs).map(row)),
  );
  routes.get("/assistants/:id", (c) => c.json(row(c.req.param("id"))));
  routes.get("/assistants/:id/graph", async (c) => {
    const graph = await graphs[c.req.param("id")];
    if (!graph) return c.json({ error: "not_found" }, 404);
    return c.json((await graph.getGraphAsync({})).toJSON());
  });
  routes.get("/assistants/:id/schemas", (c) =>
    c.json({
      graph_id: c.req.param("id"),
      input_schema: null,
      output_schema: null,
      state_schema: null,
      config_schema: null,
    }),
  );
  return routes;
}

export function createAgentApi({
  graph,
  checkpointer,
  threads,
  token,
  prefix,
}: {
  graph: EmbedOptions["graph"];
  checkpointer: BaseCheckpointSaver;
  threads: ThreadSaver;
  token: string;
  prefix: string;
}) {
  const embed = createEmbedServer({ graph, checkpointer, threads });
  const assistants = assistantRoutes(graph);
  const notFound = () => Response.json({ error: "not_found" }, { status: 404 });
  const activeRuns = new Map<string, AbortController>();

  const streamRun = async (
    threadId: string,
    request: Request,
    disconnected: AbortSignal,
  ) => {
    const stop = new AbortController();
    activeRuns.set(threadId, stop);
    const forget = () => {
      if (activeRuns.get(threadId) === stop) activeRuns.delete(threadId);
    };
    const signal = AbortSignal.any([disconnected, stop.signal]);
    signal.addEventListener("abort", forget, { once: true });
    const response = await embed.fetch(new Request(request, { signal }));
    if (!response.body) {
      forget();
      return response;
    }
    return new Response(
      response.body.pipeThrough(new TransformStream({ flush: forget })),
      response,
    );
  };

  return async (request: Request): Promise<Response> => {
    const apiKey = request.headers.get("x-api-key");
    const caller =
      apiKey && sameSecret(apiKey, token)
        ? callerFromHeaders(request.headers)
        : null;
    if (!caller)
      return Response.json({ error: "unauthenticated" }, { status: 401 });

    const url = new URL(request.url);
    url.pathname = url.pathname.slice(prefix.length) || "/";
    const { pathname } = url;
    const headers = new Headers(request.headers);
    headers.delete("content-length");

    if (pathname.startsWith("/assistants")) {
      return assistants.fetch(new Request(url, request));
    }

    // The stateless /runs routes have no thread, so no owner to check.
    if (!pathname.startsWith("/threads")) return notFound();

    const threadId = THREAD_PATH.exec(pathname)?.[1];
    if (threadId && threadId !== "search") {
      const thread = await threads.get(threadId);
      if (thread?.metadata?.owner !== caller.id) return notFound();
    }

    const { method, signal } = request;
    if (method === "GET" || method === "DELETE") {
      return embed.fetch(new Request(url, { method, headers, signal }));
    }

    // Embed 1.5.8 cancels only queued runs, so Stop would leave the model running.
    if (RUN_CANCEL_PATH.test(pathname)) {
      activeRuns.get(threadId!)?.abort();
      return new Response(null, { status: 204 });
    }

    const body = (await request.json().catch(() => ({}))) as RunBody;
    let next: RunBody = body;
    if (pathname === "/threads") {
      const requested = (body as { thread_id?: string }).thread_id;
      const existing = requested ? await threads.get(requested) : null;
      if (existing && existing.metadata?.owner !== caller.id) {
        return Response.json({ error: "conflict" }, { status: 409 });
      }
      next = {
        ...body,
        metadata: { ...body.metadata, owner: caller.id, graph_id: AGENT_ID },
      };
    } else if (pathname === "/threads/search") {
      next = { ...body, metadata: { ...body.metadata, owner: caller.id } };
    } else if (THREAD_RUN_PATH.test(pathname)) {
      await threads.set(threadId!, { kind: "patch" });
      return streamRun(
        threadId!,
        new Request(url, {
          method,
          headers,
          body: JSON.stringify(withVerifiedCaller(body, caller)),
        }),
        signal,
      );
    }
    return embed.fetch(
      new Request(url, { method, headers, body: JSON.stringify(next), signal }),
    );
  };
}
```

`activeRuns` lives in the process, so a run is stoppable only on the instance that holds it. That fits the one instance every host template in `/release-setup` sets (ship, if installed). So does the runtime's `InMemoryAgentRunner`.

## `server/persistence.ts`

The default store. A file means no database at all, and context survives a process restart.

```ts
import { mkdirSync } from "node:fs";
import path from "node:path";
import Database from "better-sqlite3";
import { SqliteSaver } from "@langchain/langgraph-checkpoint-sqlite";
import type { ThreadSaver } from "@langchain/langgraph-api/experimental/embed";

type Metadata = Record<string, unknown>;

interface ThreadRow {
  thread_id: string;
  metadata: string;
  created_at: string;
  updated_at: string;
}

function toThread(row: ThreadRow) {
  return {
    thread_id: row.thread_id,
    metadata: JSON.parse(row.metadata) as Metadata,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function matches(metadata: Metadata, filter: Metadata | undefined): boolean {
  return Object.entries(filter ?? {}).every(
    ([key, value]) => metadata[key] === value,
  );
}

function sqliteThreads(db: Database.Database): ThreadSaver {
  db.exec(`CREATE TABLE IF NOT EXISTS threads (
    thread_id TEXT PRIMARY KEY,
    metadata TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`);
  const select = db.prepare<[string], ThreadRow>(
    "SELECT * FROM threads WHERE thread_id = ?",
  );
  const upsert = db.prepare<[string, string, string, string]>(
    `INSERT INTO threads VALUES (?, ?, ?, ?)
     ON CONFLICT(thread_id) DO UPDATE SET metadata = excluded.metadata, updated_at = excluded.updated_at`,
  );
  return {
    // The embed routes read `thread == null` as not found, whatever the type says.
    get: async (id) => {
      const row = select.get(id);
      return (row ? toThread(row) : null) as never;
    },
    set: async (id, { metadata }) => {
      const now = new Date().toISOString();
      const row = select.get(id);
      const merged = {
        ...(row ? (JSON.parse(row.metadata) as Metadata) : {}),
        ...metadata,
      };
      upsert.run(id, JSON.stringify(merged), row?.created_at ?? now, now);
      return toThread(select.get(id)!);
    },
    delete: async (id) => {
      db.prepare("DELETE FROM threads WHERE thread_id = ?").run(id);
    },
    search: async function* ({ metadata, limit, offset, sortBy, sortOrder }) {
      const direction = sortOrder === "asc" ? "ASC" : "DESC";
      const rows = db
        .prepare<[], ThreadRow>(
          `SELECT * FROM threads ORDER BY ${sortBy === "updated_at" ? "updated_at" : "created_at"} ${direction}`,
        )
        .all()
        .map(toThread)
        .filter((thread) => matches(thread.metadata, metadata));
      for (const thread of rows.slice(offset, offset + limit)) {
        yield { thread, total: rows.length };
      }
    },
  };
}

/** shortcut: one SQLite file, one instance; a redeploy without a volume loses it. Move to Postgres or D1 through /release-setup. */
export function createPersistence(dataDir: string) {
  mkdirSync(dataDir, { recursive: true });
  const db = new Database(path.join(dataDir, "agent.db"));
  return { checkpointer: new SqliteSaver(db), threads: sqliteThreads(db) };
}
```

## `server/main.ts`

```ts
import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { graph } from "../agent";
import { loadEnv } from "../config/env";
import { AGENT_ID } from "@repo/shared";
import { createAgentApi } from "./agent-api";
import { app as copilotkit } from "./copilotkit";
import { createPersistence } from "./persistence";

const env = loadEnv();
const AGENT_API_PREFIX = "/langgraph";

const handleAgentApi = createAgentApi({
  graph: { [AGENT_ID]: graph },
  ...createPersistence(env.DATA_DIR),
  token: env.INTERNAL_API_TOKEN,
  prefix: AGENT_API_PREFIX,
});

const app = new Hono();
app.get("/ok", (c) => c.json({ ok: true }));
app.all(`${AGENT_API_PREFIX}/*`, (c) => handleAgentApi(c.req.raw));
app.route("/", copilotkit);

serve({ fetch: app.fetch, port: env.PORT, hostname: "0.0.0.0" }, ({ port }) => {
  console.log(`agent server on :${port}`);
});
```

## Changes to the other agent files

- **`server/copilotkit.ts`.** The adapter speaks HTTP, so it reaches the embedded API over loopback: `const AGENT_API_URL = `http://127.0.0.1:${env.PORT}/langgraph`;`. Everything else stays: `verifiedHeaders`, `identifyUser`, `filterRunRequest`, `handleThreadRoute`, `keepStoppedAnswer`, the `cors` option.
- **`auth/identity.ts`.** `sameSecret` hashes both sides and compares with `timingSafeEqual`. `callerHeaders`, `callerFromHeaders` and `readTrustedCaller` keep their shape, because `langgraph_auth_user` keeps its name. `auth/auth.ts` and `langgraph.json` do not exist.
- **`agent.ts` tail.** The graph file exports a copy whose `streamEvents` adds the per-turn trace handler, since the server compiles once:

```ts
const bound = agent.graph.withConfig({ recursionLimit: RECURSION_LIMIT });

// The embed server compiles once, so the per-turn trace handler joins at the run's stream call.
export const graph = Object.create(bound) as typeof bound;
graph.streamEvents = ((
  input: Parameters<typeof bound.streamEvents>[0],
  options: LangGraphRunnableConfig,
) =>
  bound.streamEvents.call(graph, input, {
    ...options,
    callbacks: buildTraceCallbacks(env, options.configurable),
  } as never)) as unknown as typeof bound.streamEvents;
```

- **Env schema.** Add `PORT` (default `2024`) and `DATA_DIR` (default `.data`, gitignored). Remove any deployment URL: the server talks to itself.

## `package.json`

`apps/agent/package.json` on L2 (`layouts.md`):

```json
{
  "name": "agent",
  "type": "module",
  "scripts": {
    "dev": "tsx watch --env-file=../../.env src/server/main.ts",
    "build": "tsup",
    "start": "node dist-server/main.mjs"
  },
  "dependencies": { "@repo/shared": "workspace:*" }
}
```

`apps/agent/tsup.config.ts`. `noExternal` is what inlines `@repo/shared`: it ships TypeScript source, so left as an import it fails at runtime. Every other package stays external, as `--packages=external` did:

```ts
import { defineConfig } from "tsup";

export default defineConfig({
  entry: { main: "src/server/main.ts" },
  format: ["esm"],
  platform: "node",
  outDir: "dist-server",
  outExtension: () => ({ js: ".mjs" }),
  clean: true,
  noExternal: [/^@repo\//],
});
```

Built on 2026-11-06 with tsup 9.0.0, booted from a `pnpm deploy` folder with `better-sqlite3` loading: no `@repo/shared` import was left in `dist-server/main.mjs`.

`pnpm-workspace.yaml` at the root carries `onlyBuiltDependencies: [better-sqlite3, esbuild]`.

On an existing L1 repo the scripts stay in the one `package.json`: `"dev:agent": "tsx watch --env-file=.env <agent src>/server/main.ts"`, `"dev:web": "vite"`, `"dev"` running both through `concurrently`, `"build": "vite build"`, and `"build:server": "esbuild <agent src>/server/main.ts --bundle --platform=node --format=esm --packages=external --outfile=dist-server/main.mjs"`.

Dependencies, pinned exactly: `@langchain/langgraph-api`, `@langchain/langgraph-checkpoint-sqlite`, `better-sqlite3`, `hono`, `@hono/node-server`. Dev: `tsup`, `tsx`, `@types/better-sqlite3`. `@langchain/langgraph-cli` is not used. Without `onlyBuiltDependencies`, pnpm skips the better-sqlite3 build and the server fails at boot looking for its native binary.

## Tests

Unit, in the `__tests__/` beside each file, with a fake graph:

- `agent-api`: no token → 401; a wrong token → 401; a token with no caller headers → 401; `/runs/stream` with a valid token → 404; a second caller's thread → 404 on read, run and delete; `POST /threads` with another caller's id → 409; search returns only the caller's threads whatever the body's `metadata` says; a run body with a forged `langgraph_auth_user` reaches the graph with the verified one; a cancel aborts the live run's signal, and a cancel with no live run → 204.
- `persistence`: a `set` merges metadata and keeps `created_at`; `get` of an unknown id → `null`; `search` filters on `owner`, sorts, and returns `total`; a second `createPersistence` on the same folder reads the first one's threads.

Live, with the fake model of `rules/chat-threads.md` § Tests:

| Check                                                             | Expect                                                                                            |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| One turn, then restart the process, then a follow-up              | The model's request holds the first turn                                                          |
| Second send while a run is live                                   | `RUN_ERROR` `THREAD_ALREADY_RUNNING`, and `/ok` still answers 200                                 |
| `POST /api/copilotkit/agent/assistant/stop/<threadId>` mid-answer | `{"stopped":true…}`, the fake model sees its connection closed, the next send answers             |
| Client drops the connection with no Stop                          | The run continues on the server (`InMemoryAgentRunner` is built for reconnects), it is not a Stop |
