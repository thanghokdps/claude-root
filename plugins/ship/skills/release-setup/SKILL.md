---
effort: high
name: release-setup
description: Makes a repo deployable on the host the user picks — asks where the server runs, then the database that fits that host, then login, shows the files it will generate for approval, writes the config, runs the image, and deploys after a yes. Supports Render, Railway, Cloudflare Containers and native Cloudflare Workers (a Hono or fetch-handler Worker with D1, R2, Durable Objects and Queues), with the assistant skeleton's three shapes built in. Use when a repo has never been deployed, when choosing a host or a database for it, or when a new skeleton should go live.
when_to_use: first deploy of a repo, "setup release", "deploy lên đâu", "deploy lên Render / Railway / Cloudflare", "chọn host", "chọn database khi deploy", "tạo Dockerfile và config để deploy", "make this deployable", "go live", no Dockerfile or deploy config yet, /agent-architect finished a skeleton and asks where it runs
---

# release-setup — from a working repo to a running deployment

**Invoke:** `/release-setup [render | railway | cloudflare]`

`/release-checklist` releases something that already deploys. This skill is the step before it: it makes the first deploy possible and proves it. A choice is only done when the codebase runs and deploys on the chosen host, so every host choice ends in Step 6's evidence.

Read `${CLAUDE_SKILL_DIR}/references/services.md` before Step 2. For an assistant repo also read `${CLAUDE_SKILL_DIR}/references/agent.md`.

## Step 1 — Read the repo (silent)

Find the deployable parts and what already exists: `Dockerfile`, `render.yaml`, `.railway/railway.ts`, `wrangler.jsonc`, the web build output, the server's start command, the health path, `.env.example` for the variable names. Never read `.env`.

- `apps/agent/package.json` lists `@mastra/core` or `@langchain/langgraph` → the monorepo shape in `agent.md`. The root `package.json` lists one of them → the one-package shape in `agent.md` § One-package repos.
- `wrangler.jsonc` (or `wrangler.toml`) with a `main` script and no Node server start command, such as a Hono app on Workers → the Workers shape in `services.md` § Cloudflare Workers. It has no image: skip the container steps.
- A repo with no server and no web build → say so and stop; nothing deploys yet.

## Step 2 — Ask, one question per turn, in this order

Use `AskUserQuestion` with the recommended option first. Skip what the request or the repo already answers. Never ask for a secret's value in chat.

1. **Where does the server run?** Render (Recommended), Railway or Cloudflare Containers, each with the cost line of `services.md` § Choosing. The web client follows the server to the same host. A repo already in the Workers shape gets Cloudflare Workers as the first option instead, and its environments (dev, staging, production) become the question.
2. **Does it need a database?** The options come from the host, never from a fixed list (`services.md` § Database by host): Cloudflare → D1, Render or Railway → Postgres, or no database. Say what each one means, in these words:
   - **With a database:** threads and context survive a restart and a redeploy.
   - **No database:** threads live in a file on the server, as `mastra-ai/ui-dojo` does. Context survives a process restart. A redeploy loses it unless the host gives a volume (`services.md` § File storage).
3. **Who may use it?** (assistant repos, or any repo with no login) The options of `agent.md` § Login: a shared password for a demo (Recommended for a first deploy), or a real login provider, which goes through `/agent-feature` (ai, if installed) before this skill continues.

## Step 3 — Show what will change, ask for approval

List every file to create or change with one line each, the variables the host needs (names only), and what the host will charge. Ask to approve with `AskUserQuestion`. Nothing is written before the yes.

## Step 4 — Generate

Write only the files of the approved list, from the templates in `services.md`, and from `agent.md` for an assistant. Resolve every version and every base image digest at generation time, never from memory. Then, in order:

1. The repo's own checks pass: format, typecheck, lint, tests.
2. Build the image, run it with fake or local values, and check it: the health path answers, the process runs as non-root, and data survives a container recreate on a volume. For the Workers shape instead: `wrangler deploy --dry-run --env <env>` compiles for each environment, and `wrangler dev` with local D1 answers the health path and serves the SPA.
3. Record the host, database and login in the repo's `RELEASE.md`, with the deploy command and the rollback command, so `/release-checklist` picks them up.

**Done when:** the image runs and passes its health check (Workers shape: the dry run passes for every environment and `wrangler dev` answers the health path), and `RELEASE.md` exists.

## Step 5 — Deploy, after a yes

Deploying changes something outside the repo, so it needs its own yes. Show the exact command and what it creates. The user signs in to the host and sets the secrets, in the dashboard or the host's CLI: never type a key, password or token into a form or a command. A secret is generated with a command the user runs, and never shown in a reply.

## Step 6 — Prove it on the deployed URL

Run these against the real URL and show each result:

| Check                                                                    | Expect                                  |
| ------------------------------------------------------------------------ | --------------------------------------- |
| Health path                                                              | 200, no secret or version in the body   |
| A request with no password or login                                      | 401                                     |
| One real turn or the headline request, from the deployed web page        | Works, spread over time when it streams |
| An `OPTIONS` from another origin                                         | Never echoes that origin                |
| Redeploy, then reopen the same thread (only with a database or a volume) | History and context still there         |

**Done when:** every row has its evidence. For an assistant, then run the rows of `production.md` (ai, if installed) that apply. A row that cannot run yet is listed with why, never skipped silently.

## Rules

- Never `git push`, deploy, or change a host setting without a yes for that action.
- Never bake a secret into an image, a config file or a `VITE_*` variable. Everything in `dist/` is public.
- A file on a container disk is not durable. Say so whenever the user picks no database.
- Report a host whose limits break the app before generating, such as a plan with too little memory or no volume.
- `Cloudflare Workers` without containers cannot run a Node server (Express, NestJS, a LangGraph or Mastra server). Offer Containers, or stop. Only an app written for Workers takes the Workers shape.

## Hand-offs

Later releases → `/release-checklist`. A CI job for the deploy → `/pipeline` (devops, if installed). A Dockerfile for a repo with no template here → `/container` (devops, if installed). A real login → `/agent-feature` (ai, if installed).
