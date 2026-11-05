# Assistant repos — what a deploy adds

Read by `/release-setup` for a repo with `src/langchain/`, `src/langgraph/` or `src/mastra/`. Everything on shapes A and B assumes the embed server (`embed-server.md`, ai, if installed): `src/<folder>/server/main.ts` with `/ok`, and `createPersistence` in `server/persistence.ts`.

A repo still on `langgraph.json` has no production server: move it to the embed server first, through `/agent-architect` (ai, if installed).

Run live on 2026-11-05 on Node 24 with a fake model: § Login in a browser (wrong password, right password, streaming, Stop, reload), § Postgres on Postgres 17 in Docker, § D1 through a real Worker on `wrangler dev --local` 4.157.0, and the images as non-root: shape A at about 255 MiB of memory and shape M at about 320 MiB. Shape B ran on the embed server without an image of its own; it is the same server. No host was deployed to.

## Shapes

| Shape | Server                                                        | Health    | Store with no database                | Store with a database               |
| ----- | ------------------------------------------------------------- | --------- | ------------------------------------- | ----------------------------------- |
| A, B  | `node dist-server/main.mjs`, port `PORT`                      | `/ok`     | SQLite, `DATA_DIR/agent.db`           | § Postgres or § D1                  |
| M     | `mastra build`, then `node .mastra/output/index.mjs`, default | `/health` | `LibSQLStore` on a file, as `ui-dojo` | `LibSQLStore` on Turso, or Postgres |

On shape M, `@mastra/libsql` takes `url: "file:<path>"` for a file and a Turso URL plus token for a remote database, as `mastra-ai/ui-dojo` `src/mastra/storage.ts` switches on `TURSO_DATABASE_URL`. D1 has no stock Mastra store: on Cloudflare offer Turso, or stop. Confirm the current package names on the Mastra docs at generation time.

## Login

A deployed page with no login is an open model key. `DEV_USER_ID` is refused in production, so `resolveCaller` returns no caller and every request gets 401 until one of these exists.

**Shared password, for a demo.** Add `DEMO_PASSWORD` to the env schema (`z.string().min(16).optional()`). The user generates it and sets it on the host. It goes in `x-demo-password`, because the runtime's CORS answers `allow-headers: *`, which a browser does not extend to `Authorization` (Fetch standard, unverified here, from memory; the header name avoids the question).

```ts
export function resolveCaller(request: Request, env: Env): Caller | null {
  if (env.DEMO_PASSWORD) {
    const password = request.headers.get("x-demo-password");
    if (!password || !sameSecret(password, env.DEMO_PASSWORD)) return null;
    // shortcut: one shared identity, so everyone shares threads; replace with a real login before real users.
    return { id: "demo", name: "Demo user", timeZone: env.DEV_USER_TIMEZONE };
  }
  if (env.NODE_ENV === "production" || !env.DEV_USER_ID) return null;
  return {
    id: env.DEV_USER_ID,
    name: env.DEV_USER_NAME ?? env.DEV_USER_ID,
    timeZone: env.DEV_USER_TIMEZONE,
  };
}
```

On the web side, a small page asks for the password and keeps it in `sessionStorage`. The password never enters a `VITE_*` variable: everything in `dist/` is public. Run in a browser on 2026-11-05: a wrong password stays on the page with "Wrong password.", the right one opens the chat, and streaming, Stop and history all carry it. `src/lib/demo-password.ts`:

```ts
const STORAGE_KEY = "demo-password";

export function readDemoPassword(): string | null {
  try {
    return sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function saveDemoPassword(password: string): void {
  try {
    sessionStorage.setItem(STORAGE_KEY, password);
  } catch {
    // Private mode: the gate asks again on the next load.
  }
}

export function clearDemoPassword(): void {
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing stored.
  }
}

export function demoHeaders(): Record<string, string> {
  const password = readDemoPassword();
  return password ? { "x-demo-password": password } : {};
}
```

`src/components/password-gate.tsx` probes the thread list, so a server with no password opens straight away. A locked page logs one 401 in the console; the probe has no other way to ask.

```tsx
import { useCallback, useEffect, useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { RUNTIME_URL } from "@/constants";
import {
  clearDemoPassword,
  demoHeaders,
  saveDemoPassword,
} from "@/lib/demo-password";

type GateStatus = "checking" | "open" | "locked" | "wrong" | "unreachable";

export function PasswordGate({
  children,
}: {
  children: ReactNode;
}): React.JSX.Element {
  const [status, setStatus] = useState<GateStatus>("checking");
  const [password, setPassword] = useState("");

  const check = useCallback(async (attempted: boolean) => {
    try {
      const response = await fetch(`${RUNTIME_URL}/app-threads`, {
        headers: demoHeaders(),
      });
      if (response.status !== 401) return setStatus("open");
      clearDemoPassword();
      setStatus(attempted ? "wrong" : "locked");
    } catch {
      setStatus("unreachable");
    }
  }, []);

  useEffect(() => {
    void check(false);
  }, [check]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    saveDemoPassword(password);
    void check(true);
  };

  if (status === "open") return <>{children}</>;
  if (status === "checking") return <p role="status">Checking access…</p>;
  if (status === "unreachable") {
    return <p role="alert">The assistant can't be reached.</p>;
  }
  return (
    <form onSubmit={submit}>
      <label htmlFor="demo-password">Password</label>
      <input
        id="demo-password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      <button type="submit">Open</button>
      {status === "wrong" && <p role="alert">Wrong password.</p>}
    </form>
  );
}
```

`<CopilotKit headers={demoHeaders()} …>` goes in a child of the gate, never above it: a provider rendered before the gate opens computes its headers with no password. Every `fetch` in `lib/threads-api.ts` sends `demoHeaders()` too.

```tsx
// Its own component: it renders only once the gate opens, so the headers hold the password.
function Chat(): React.JSX.Element {
  return (
    <CopilotKit
      runtimeUrl={RUNTIME_URL}
      agent={AGENT_ID}
      headers={demoHeaders()}
    >
      {/* the router and pages */}
    </CopilotKit>
  );
}

export function App(): React.JSX.Element {
  return (
    <PasswordGate>
      <Chat />
    </PasswordGate>
  );
}
```

**A real login.** `/agent-feature` (ai, if installed) builds it, with `resolveCaller` as the one place that changes. It runs before this skill continues.

## Dockerfile

Pin the base image by digest at generation time. `pnpm prune` keeps `better-sqlite3`'s built binary. `package.json` must name `packageManager` exactly: without it, `corepack` in the image takes the newest pnpm, which failed `pnpm install` with `ERR_PNPM_MINIMUM_RELEASE_AGE_VIOLATION` and ignored the `pnpm` field (run on 2026-11-05).

```dockerfile
FROM node:24-slim AS build
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY tsconfig*.json ./
COPY src ./src
RUN pnpm build:server
RUN pnpm prune --prod --ignore-scripts

FROM node:24-slim
ENV NODE_ENV=production
ENV DATA_DIR=/data
WORKDIR /app
COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist-server ./dist-server
RUN mkdir /data && chown node:node /data
USER node
EXPOSE 2024
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||2024)+'/ok').then(r=>process.exit(r.ok?0:1),()=>process.exit(1))"
CMD ["node", "dist-server/main.mjs"]
```

`.dockerignore`:

```
node_modules
dist
dist-server
.data
.git
.env*
!.env.example
```

Shape M, run as an image with `mastra` 1.38.0 and `@mastra/libsql` 1.29.0 (635 MB; `/data/mastra.db` created as non-root). `mastra build` installs the output's own `node_modules`, so it runs inside the image:

```dockerfile
FROM node:24-slim AS build
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY src ./src
RUN pnpm mastra build

FROM node:24-slim
ENV NODE_ENV=production
ENV DATA_DIR=/data
WORKDIR /app
COPY --from=build /app/.mastra/output ./
RUN mkdir /data && chown node:node /data
USER node
EXPOSE 4111
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||4111)+'/health').then(r=>process.exit(r.ok?0:1),()=>process.exit(1))"
CMD ["node", "index.mjs"]
```

## Postgres

Add `@langchain/langgraph-checkpoint-postgres` and `pg`, pinned, plus `DATABASE_URL` in the env schema. Replace `server/persistence.ts` and its call: `...(await createPersistence(env.DATABASE_URL))`. Delete the SQLite dependencies.

```ts
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";
import type { ThreadSaver } from "@langchain/langgraph-api/experimental/embed";
import { Pool } from "pg";

type Metadata = Record<string, unknown>;

interface ThreadRow {
  thread_id: string;
  metadata: Metadata;
  created_at: Date;
  updated_at: Date;
}

const toThread = (row: ThreadRow) => ({
  thread_id: row.thread_id,
  metadata: row.metadata,
  created_at: row.created_at.toISOString(),
  updated_at: row.updated_at.toISOString(),
});

function postgresThreads(pool: Pool): ThreadSaver {
  return {
    // The embed routes read `thread == null` as not found, whatever the type says.
    get: async (id) => {
      const { rows } = await pool.query<ThreadRow>(
        "SELECT * FROM threads WHERE thread_id = $1",
        [id],
      );
      return (rows[0] ? toThread(rows[0]) : null) as never;
    },
    set: async (id, { metadata }) => {
      const { rows } = await pool.query<ThreadRow>(
        `INSERT INTO threads (thread_id, metadata) VALUES ($1, $2)
         ON CONFLICT (thread_id) DO UPDATE
         SET metadata = threads.metadata || excluded.metadata, updated_at = now()
         RETURNING *`,
        [id, metadata ?? {}],
      );
      return toThread(rows[0]!);
    },
    delete: async (id) => {
      await pool.query("DELETE FROM threads WHERE thread_id = $1", [id]);
    },
    search: async function* ({ metadata, limit, offset, sortBy, sortOrder }) {
      const column = sortBy === "updated_at" ? "updated_at" : "created_at";
      const direction = sortOrder === "asc" ? "ASC" : "DESC";
      const { rows } = await pool.query<ThreadRow & { total: string }>(
        `SELECT *, count(*) OVER() AS total FROM threads WHERE metadata @> $1
         ORDER BY ${column} ${direction} LIMIT $2 OFFSET $3`,
        [metadata ?? {}, limit, offset],
      );
      for (const row of rows) {
        yield { thread: toThread(row), total: Number(row.total) };
      }
    },
  };
}

export async function createPersistence(databaseUrl: string) {
  const pool = new Pool({ connectionString: databaseUrl });
  await pool.query(`CREATE TABLE IF NOT EXISTS threads (
    thread_id TEXT PRIMARY KEY,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
  )`);
  const checkpointer = new PostgresSaver(pool);
  await checkpointer.setup();
  return { checkpointer, threads: postgresThreads(pool) };
}
```

## D1

A container has no D1 binding, so the Worker in front holds it and offers a bridge at `/internal/d1`, guarded by `INTERNAL_API_TOKEN`. The server calls that bridge with `D1_BRIDGE_URL`, the Worker's own URL plus `/internal/d1`. There is no stock D1 checkpointer, so the saver below is the kit's own. Replace `server/persistence.ts`, and call `createPersistence(env.D1_BRIDGE_URL, env.INTERNAL_API_TOKEN)`.

### Migration

`worker/migrations/0001_init.sql`, applied by `wrangler d1 migrations apply <app> --remote` after a yes:

```sql
CREATE TABLE IF NOT EXISTS threads (
  thread_id TEXT PRIMARY KEY,
  metadata TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS checkpoints (
  thread_id TEXT NOT NULL,
  checkpoint_ns TEXT NOT NULL DEFAULT '',
  checkpoint_id TEXT NOT NULL,
  parent_checkpoint_id TEXT,
  type TEXT NOT NULL,
  checkpoint TEXT NOT NULL,
  metadata TEXT NOT NULL,
  PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
CREATE TABLE IF NOT EXISTS checkpoint_writes (
  thread_id TEXT NOT NULL,
  checkpoint_ns TEXT NOT NULL DEFAULT '',
  checkpoint_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  idx INTEGER NOT NULL,
  channel TEXT NOT NULL,
  type TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
);
```

### Bridge, in the Worker

```ts
type Statement = { sql: string; params?: (string | number | null)[] };

async function digest(text: string): Promise<ArrayBuffer> {
  return crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
}

async function handleD1Bridge(request: Request, env: Env): Promise<Response> {
  if (request.method !== "POST" || !env.DB) {
    return new Response(null, { status: 404 });
  }
  const given = await digest(request.headers.get("x-api-key") ?? "");
  const expected = await digest(env.INTERNAL_API_TOKEN);
  if (!crypto.subtle.timingSafeEqual(given, expected)) {
    return new Response(null, { status: 401 });
  }
  const { statements } = (await request.json()) as { statements: Statement[] };
  const results = await env.DB.batch(
    statements.map(({ sql, params = [] }) =>
      env.DB.prepare(sql).bind(...params),
    ),
  );
  return Response.json(results.map((result) => result.results));
}
```

The bridge runs any SQL it is sent, so the token is the whole defence. It is the same `INTERNAL_API_TOKEN` as the agent API, and never reaches the browser.

### Saver and threads

```ts
import {
  BaseCheckpointSaver,
  copyCheckpoint,
} from "@langchain/langgraph-checkpoint";
import type {
  Checkpoint,
  CheckpointListOptions,
  CheckpointMetadata,
  CheckpointTuple,
  PendingWrite,
} from "@langchain/langgraph-checkpoint";
import type { ThreadSaver } from "@langchain/langgraph-api/experimental/embed";
import type { RunnableConfig } from "@langchain/core/runnables";

type Metadata = Record<string, unknown>;
type Row = Record<string, string | number | null>;
type Statement = { sql: string; params?: (string | number | null)[] };
export type Bridge = (statements: Statement[]) => Promise<Row[][]>;

/** Calls the Worker that holds the D1 binding: a container has no binding of its own. */
export function createBridge(url: string, token: string): Bridge {
  return async (statements) => {
    const response = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json", "x-api-key": token },
      body: JSON.stringify({ statements }),
    });
    if (!response.ok) throw new Error(`D1 bridge failed: ${response.status}`);
    return (await response.json()) as Row[][];
  };
}

const toBase64 = (bytes: Uint8Array) => Buffer.from(bytes).toString("base64");
const fromBase64 = (text: string) =>
  new Uint8Array(Buffer.from(text, "base64"));

function configIds(config: RunnableConfig) {
  const { thread_id, checkpoint_ns, checkpoint_id } = config.configurable ?? {};
  if (typeof thread_id !== "string") throw new Error("thread_id is required");
  return {
    threadId: thread_id,
    ns: typeof checkpoint_ns === "string" ? checkpoint_ns : "",
    checkpointId: checkpoint_id as string | undefined,
  };
}

export class D1Saver extends BaseCheckpointSaver {
  constructor(private readonly bridge: Bridge) {
    super();
  }

  private async toTuple(row: Row): Promise<CheckpointTuple> {
    const thread_id = String(row.thread_id);
    const checkpoint_ns = String(row.checkpoint_ns);
    const checkpoint_id = String(row.checkpoint_id);
    const [writes] = await this.bridge([
      {
        sql: "SELECT * FROM checkpoint_writes WHERE thread_id = ? AND checkpoint_ns = ? AND checkpoint_id = ? ORDER BY task_id, idx",
        params: [thread_id, checkpoint_ns, checkpoint_id],
      },
    ]);
    const pendingWrites = await Promise.all(
      (writes ?? []).map(async (write): Promise<[string, string, unknown]> => [
        String(write.task_id),
        String(write.channel),
        await this.serde.loadsTyped(
          String(write.type),
          fromBase64(String(write.value)),
        ),
      ]),
    );
    return {
      config: { configurable: { thread_id, checkpoint_ns, checkpoint_id } },
      checkpoint: (await this.serde.loadsTyped(
        String(row.type),
        fromBase64(String(row.checkpoint)),
      )) as Checkpoint,
      metadata: JSON.parse(String(row.metadata)) as CheckpointMetadata,
      parentConfig: row.parent_checkpoint_id
        ? {
            configurable: {
              thread_id,
              checkpoint_ns,
              checkpoint_id: String(row.parent_checkpoint_id),
            },
          }
        : undefined,
      pendingWrites,
    };
  }

  async getTuple(config: RunnableConfig): Promise<CheckpointTuple | undefined> {
    const { threadId, ns, checkpointId } = configIds(config);
    const [rows] = await this.bridge([
      {
        sql: `SELECT * FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ?
              ${checkpointId ? "AND checkpoint_id = ?" : "ORDER BY checkpoint_id DESC LIMIT 1"}`,
        params: [threadId, ns, ...(checkpointId ? [checkpointId] : [])],
      },
    ]);
    return rows?.[0] ? this.toTuple(rows[0]) : undefined;
  }

  async *list(
    config: RunnableConfig,
    options?: CheckpointListOptions,
  ): AsyncGenerator<CheckpointTuple> {
    const { threadId, ns } = configIds(config);
    const before = options?.before?.configurable?.checkpoint_id as
      string | undefined;
    const [rows] = await this.bridge([
      {
        sql: `SELECT * FROM checkpoints WHERE thread_id = ? AND checkpoint_ns = ?
              ${before ? "AND checkpoint_id < ?" : ""}
              ORDER BY checkpoint_id DESC ${options?.limit ? "LIMIT ?" : ""}`,
        params: [
          threadId,
          ns,
          ...(before ? [before] : []),
          ...(options?.limit ? [options.limit] : []),
        ],
      },
    ]);
    for (const row of rows ?? []) yield this.toTuple(row);
  }

  async put(
    config: RunnableConfig,
    checkpoint: Checkpoint,
    metadata: CheckpointMetadata,
  ): Promise<RunnableConfig> {
    const { threadId, ns, checkpointId } = configIds(config);
    const [type, value] = await this.serde.dumpsTyped(
      copyCheckpoint(checkpoint),
    );
    await this.bridge([
      {
        sql: `INSERT OR REPLACE INTO checkpoints
              (thread_id, checkpoint_ns, checkpoint_id, parent_checkpoint_id, type, checkpoint, metadata)
              VALUES (?, ?, ?, ?, ?, ?, ?)`,
        params: [
          threadId,
          ns,
          checkpoint.id,
          checkpointId ?? null,
          type,
          toBase64(value),
          JSON.stringify(metadata),
        ],
      },
    ]);
    return {
      configurable: {
        thread_id: threadId,
        checkpoint_ns: ns,
        checkpoint_id: checkpoint.id,
      },
    };
  }

  async putWrites(
    config: RunnableConfig,
    writes: PendingWrite[],
    taskId: string,
  ): Promise<void> {
    const { threadId, ns, checkpointId } = configIds(config);
    const statements = await Promise.all(
      writes.map(async ([channel, value], idx) => {
        const [type, bytes] = await this.serde.dumpsTyped(value);
        return {
          sql: `INSERT OR REPLACE INTO checkpoint_writes
                (thread_id, checkpoint_ns, checkpoint_id, task_id, idx, channel, type, value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
          params: [
            threadId,
            ns,
            checkpointId ?? "",
            taskId,
            idx,
            channel,
            type,
            toBase64(bytes),
          ],
        };
      }),
    );
    await this.bridge(statements);
  }

  async deleteThread(threadId: string): Promise<void> {
    await this.bridge([
      {
        sql: "DELETE FROM checkpoints WHERE thread_id = ?",
        params: [threadId],
      },
      {
        sql: "DELETE FROM checkpoint_writes WHERE thread_id = ?",
        params: [threadId],
      },
    ]);
  }
}

function toThread(row: Row) {
  return {
    thread_id: String(row.thread_id),
    metadata: JSON.parse(String(row.metadata)) as Metadata,
    created_at: String(row.created_at),
    updated_at: String(row.updated_at),
  };
}

function d1Threads(bridge: Bridge): ThreadSaver {
  const read = async (id: string) => {
    const [rows] = await bridge([
      { sql: "SELECT * FROM threads WHERE thread_id = ?", params: [id] },
    ]);
    return rows?.[0] ? toThread(rows[0]) : null;
  };
  return {
    // The embed routes read `thread == null` as not found, whatever the type says.
    get: async (id) => (await read(id)) as never,
    set: async (id, { metadata }) => {
      const now = new Date().toISOString();
      const existing = await read(id);
      const merged = { ...existing?.metadata, ...metadata };
      await bridge([
        {
          sql: `INSERT INTO threads VALUES (?, ?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET metadata = excluded.metadata, updated_at = excluded.updated_at`,
          params: [
            id,
            JSON.stringify(merged),
            existing?.created_at ?? now,
            now,
          ],
        },
      ]);
      return (await read(id))!;
    },
    delete: async (id) => {
      await bridge([
        { sql: "DELETE FROM threads WHERE thread_id = ?", params: [id] },
      ]);
    },
    search: async function* ({ metadata, limit, offset, sortBy, sortOrder }) {
      const owner = metadata?.owner;
      const filter = typeof owner === "string" ? owner : "";
      const column = sortBy === "updated_at" ? "updated_at" : "created_at";
      const direction = sortOrder === "asc" ? "ASC" : "DESC";
      const [rows, totals] = await bridge([
        {
          sql: `SELECT * FROM threads WHERE json_extract(metadata, '$.owner') = ?
                ORDER BY ${column} ${direction} LIMIT ? OFFSET ?`,
          params: [filter, limit, offset],
        },
        {
          sql: "SELECT count(*) AS total FROM threads WHERE json_extract(metadata, '$.owner') = ?",
          params: [filter],
        },
      ]);
      for (const row of rows ?? []) {
        yield { thread: toThread(row), total: Number(totals?.[0]?.total ?? 0) };
      }
    },
  };
}

export function createPersistence(url: string, token: string) {
  const bridge = createBridge(url, token);
  return { checkpointer: new D1Saver(bridge), threads: d1Threads(bridge) };
}
```

Every checkpoint is a round trip through the Worker, so a turn is slower than on Postgres. Search by `owner` is the only filter the guard sends, which is why this `search` reads only that key.
