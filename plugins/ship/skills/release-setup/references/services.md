# Services — what each host needs

Read by `/release-setup`. Every template is a starting point: confirm field names on the host's current docs at generation time, and write the date you checked into `RELEASE.md`.

Checked on 2026-11-05 against render.com/docs/blueprint-spec, docs.railway.com/infrastructure-as-code and its reference, the `railway` npm package 3.16.0 `dist/index-*.d.ts`, and developers.cloudflare.com/containers. A Node server image on `node:24-slim` used about 255 MiB of memory at idle.

## Choosing

| Host                  | Cost line for the question                                                             | Watch out for                                                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Render                | A free web service exists: it sleeps after 15 minutes idle and wakes in about a minute | A free instance's memory is tight for this image. A disk's free-plan availability is not stated, so check before promising one |
| Railway               | Priced by usage. Check the current plan before quoting a number                        | `railway.json` is deprecated and stops being read on 2026-12-01: generate `.railway/railway.ts`, never `railway.json`          |
| Cloudflare Containers | Needs Workers Paid ($5 per month). Billed by use, and sleeps when idle                 | Needs a Worker in front. Whether a container's disk survives a restart is not stated, so treat it as lost                      |

## Database by host

| Host       | Recommend                  | Code                                         |
| ---------- | -------------------------- | -------------------------------------------- |
| Render     | Render Postgres            | stock `PostgresSaver`, `agent.md` § Postgres |
| Railway    | Railway Postgres           | stock `PostgresSaver`, `agent.md` § Postgres |
| Cloudflare | D1                         | kit-written saver, `agent.md` § D1           |
| Another    | Ask which database it uses | Stop if no saver exists for it               |

## File storage

The no-database choice keeps a file on the server, in `DATA_DIR`.

| Host       | Surviving a redeploy                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------------------ |
| Render     | Needs a `disk` block. A disk removes zero-downtime deploys, and the service cannot scale               |
| Railway    | Needs a `volume`, mounted at `DATA_DIR`. Mounted at start, not during build. No replicas with a volume |
| Cloudflare | No volume to rely on. Say that a redeploy or a sleep can lose it, and offer D1                         |

## Render — `render.yaml`

`runtime: docker` builds the repo's `Dockerfile`. `sync: false` prompts for the value once, in the dashboard, so no secret enters the file.

```yaml
databases: # only with Postgres
  - name: <app>-db
    plan: free
    region: singapore

services:
  - type: web
    name: <app>-agent
    runtime: docker
    plan: free
    region: singapore
    healthCheckPath: /ok
    buildFilter:
      paths:
        - apps/agent/**
        - packages/**
        - pnpm-lock.yaml
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: INTERNAL_API_TOKEN
        generateValue: true
      - key: WEB_ORIGIN
        sync: false
      - key: DATABASE_URL # only with Postgres
        fromDatabase:
          name: <app>-db
          property: connectionString

  - type: web
    name: <app>-web
    runtime: static
    buildCommand: corepack enable && pnpm install --frozen-lockfile && pnpm --filter web build
    staticPublishPath: ./apps/web/dist
    buildFilter:
      paths:
        - apps/web/**
        - packages/**
        - pnpm-lock.yaml
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
    envVars:
      - key: VITE_LANGGRAPH_BASE_URL
        sync: false
```

`buildFilter` is what makes the two services release apart: a change under `apps/web` leaves the agent alone (render.com/docs/blueprint-spec, checked on 2026-11-06; paths are relative to the repo root). On a one-package repo, drop it and use `pnpm build` with `./dist`.

Set `WEB_ORIGIN` and the `VITE_*` base URL after the first deploy shows the two URLs, then redeploy the web service: Vite writes `VITE_*` into the bundle at build time.

With no database and a disk, add to the agent service:

```yaml
disk:
  name: data
  mountPath: /data
  sizeGB: 1
```

Deploy: the user connects the repo in the Render dashboard as a Blueprint.

## Railway — `.railway/railway.ts`

Add `railway` as an exact dev dependency. Railway builds with a Dockerfile when it finds one.

```ts
import {
  defineRailway,
  postgres,
  preserve,
  project,
  service,
} from "railway/iac";

export default defineRailway(() => {
  const db = postgres("postgres"); // only with Postgres

  const agent = service("agent", {
    build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile" },
    healthcheck: "/ok",
    env: {
      OPENAI_API_KEY: preserve(),
      INTERNAL_API_TOKEN: preserve(),
      WEB_ORIGIN: preserve(),
      DATABASE_URL: db.env.DATABASE_URL, // only with Postgres
    },
  });

  const web = service("web", {
    build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile.web" },
  });

  return project("<app>", { resources: [agent, web, db] });
});
```

`preserve()` keeps the value the user set in the dashboard. `Dockerfile.web`, at the repo root with the root as its context, runs `pnpm --filter web build` and serves `apps/web/dist/` with Caddy, falling back to `index.html`, as Railway's Vite guides do. It declares `ARG VITE_LANGGRAPH_BASE_URL` so the value reaches the build; confirm that Railway passes it, because this template has not been run on Railway.

With no database and a volume:

```ts
const data = volume("agent-data", { region: "<region>", sizeMB: 1024 });
// on the agent service:
volumeMounts: { "/data": data },
```

Deploy: `railway login`, `railway link`, `railway config plan`, then `railway config apply` after the user reads the plan.

## Cloudflare — `wrangler.jsonc` and a Worker

A container cannot take traffic alone. A Worker forwards to it, and holds the D1 binding. Containers need `@cloudflare/containers` and `wrangler`, both exact dev dependencies. The client goes to Cloudflare Pages.

```jsonc
{
  "$schema": "node_modules/wrangler/config-schema.json",
  "name": "<app>-agent",
  "main": "worker/index.ts",
  "compatibility_date": "<today>",
  "compatibility_flags": ["nodejs_compat"],
  "containers": [
    {
      "class_name": "AgentContainer",
      "image": "./Dockerfile",
      "max_instances": 1,
      "instance_type": "basic",
      "constraints": { "regions": ["APAC"] },
    },
  ],
  "durable_objects": {
    "bindings": [{ "name": "AGENT", "class_name": "AgentContainer" }],
  },
  "exports": {
    "AgentContainer": { "type": "durable-object", "storage": "sqlite" },
  },
  // only with D1
  "d1_databases": [
    {
      "binding": "DB",
      "database_name": "<app>",
      "database_id": "<from wrangler d1 create>",
      "migrations_dir": "worker/migrations",
    },
  ],
  "vars": { "WEB_ORIGIN": "https://<app>.pages.dev" },
}
```

```ts
import { Container, getContainer } from "@cloudflare/containers";

type Env = {
  AGENT: DurableObjectNamespace<AgentContainer>;
  DB?: D1Database;
  OPENAI_API_KEY: string;
  INTERNAL_API_TOKEN: string;
  WEB_ORIGIN: string;
  D1_BRIDGE_URL?: string;
};

export class AgentContainer extends Container<Env> {
  defaultPort = 2024;
  sleepAfter = "10m";
  override envVars = {
    OPENAI_API_KEY: this.env.OPENAI_API_KEY,
    INTERNAL_API_TOKEN: this.env.INTERNAL_API_TOKEN,
    WEB_ORIGIN: this.env.WEB_ORIGIN,
    ...(this.env.D1_BRIDGE_URL
      ? { D1_BRIDGE_URL: this.env.D1_BRIDGE_URL }
      : {}),
  };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (new URL(request.url).pathname === "/internal/d1") {
      return handleD1Bridge(request, env); // only with D1, agent.md § D1
    }
    return getContainer(env.AGENT).fetch(request);
  },
};
```

`handleD1Bridge` is in `agent.md` § D1. `exports` replaces the older `migrations` array, and the two cannot be combined (developers.cloudflare.com/containers/get-started). Run on `wrangler dev --local` 4.157.0 on 2026-11-05, on Colima: the config was accepted, the image built, and the container started healthy with its `envVars`. A request through the Worker then hung with no error, so the Worker-to-container path is not proven; test it on Docker Desktop or on a real deploy first. The D1 bridge ran on the same wrangler.

`database_id` comes from `wrangler d1 create <app>`, which the user runs. Add every other variable the env schema needs to `envVars` too: anything left out never reaches the container. Secrets are set by the user: `wrangler secret put OPENAI_API_KEY`.

Deploy: Docker running, then `wrangler deploy` for the agent and `wrangler pages deploy apps/web/dist --project-name <app>` for the client after `pnpm --filter web build`. `max_instances: 1` keeps one process, which the in-process thread state and run queue assume.
