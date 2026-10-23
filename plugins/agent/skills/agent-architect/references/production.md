# Production readiness — before an assistant release

Read by `/agent-architect` Step 4 (built in from the first slice) and `/agent-feature` Step 8 (checked before the PR lands). The release itself goes through `/release-checklist`; this list is what an assistant adds to its items 4, 8 and 9.

Mastra names checked against mastra.ai docs on 2026-10-23. Confirm each option on the **installed** package (`.d.ts`) before relying on it.

Each row is ✅ with evidence, ❌, or n/a with the reason. Evidence comes from the deployed environment (staging at least), never from localhost.

| # | Check | Shape A / B (LangChain · LangGraph) | Shape M (Mastra) | Evidence |
|---|-------|-------------------------------------|------------------|----------|
| 1 | **Durable state** | `PostgresSaver` from `@langchain/langgraph-checkpoint-postgres`, `setup()` run once (migration or boot). `MemorySaver` only in tests. LangGraph Platform brings its own — note it on the card | `storage: new PostgresStore({ id, connectionString })` from `@mastra/pg` on `new Mastra`. LibSQL or in-memory only in dev. `disableInit: true` when CI runs the migrations | Restart the agent server mid-thread: the thread resumes with its history, and a pending HITL approval still resumes |
| 2 | **Streaming through the proxy** | SSE response: `Content-Type: text/event-stream`, `Cache-Control: no-cache, no-transform`, `X-Accel-Buffering: no` | same | A turn through the deployed URL: events arrive spread over time, not in one burst at the end |
| 3 | **Time limits** | Every hop allows the longest turn: Next.js route `export const maxDuration` (and `runtime = 'nodejs'`) within the plan cap, proxy `proxy_read_timeout`, load-balancer idle timeout, agent run timeout | plus `server.timeout` (default 180000 ms) | p99 turn duration from tracing, below the smallest timeout in the chain with margin; a deliberately long turn ends as `RUN_FINISHED`, or as a readable `RUN_ERROR` |
| 4 | **Health endpoints** | Liveness (process up, no dependency calls) and readiness (storage reachable, required env present — never a model call). LangGraph server answers `/ok` | A `registerApiRoute` health route, unless the installed server has one | Both answer on the deployed host, unauthenticated, with no config or version secrets in the body |
| 5 | **Env reaches the agent server** | The agent server is its own process: model keys, DB URL, tracing keys and kill-switch config are set for it (`langgraph.json` `env`, container env, platform secrets), not only for the web app. The runtime forwards the caller's auth header on every request | same; `requestContext` claims set by server middleware | The env schema fails the boot with one variable removed; the target env lists every name (names only, never values); a turn's tool sees the caller's claims |
| 6 | **Fallback and kill switches set** | Fallback model configured in the target env (`modelFallbackMiddleware`, last in the chain). Kill switch per tool and per agent present in that env's config, per `optimisation.md` § Rollout safety | Fallback from the kit's `models.ts` factory or a gateway (`model` takes one model) | In staging, with the primary key invalidated, a turn answers and its trace names the fallback provider; one switched-off tool is refused |
| 7 | **Tracing on, masked** | Provider switch set for prod; masking per `${CLAUDE_PLUGIN_ROOT}/rules/agent-tracing-privacy.md` | `observability: new Observability({ configs })` from `@mastra/observability`, with `SensitiveDataFilter` in `spanOutputProcessors` (keep it in any custom config); `sampling` chosen on purpose | The smoke turn's trace exists, with model, provider, tokens and tool status; message text and tool args masked, user id hashed, no token |
| 8 | **Rollback of prompt and model** | Prompt version and model id come from config or a versioned file, and both appear in the trace. Rolling back is an env change or redeploying the previous tag, not a code revert. State the new version writes stays readable by the old one (state schema changes go through `/write-migration`) | same; Memory and storage schema included | The exact rollback command is written down and was run once in staging; a thread started on the new version continues after the rollback |

## When to run it

- **Scaffold** (`/agent-architect` Step 4): rows 1, 4, 5, 6 and 7 are built in, not added later. Row 1 can stay on dev storage until Q6 asks for durable threads, recorded as a risk on the card.
- **Feature** (`/agent-feature` Step 8): re-check the rows the diff touches — a new tool needs its kill switch (6), a new env var reaches the agent server (5), a prompt or model change has its rollback (8), a slower tool fits the time limits (3).
- **Release** (`/release-checklist`): all eight rows on the target environment, with row 8's command as the release's rollback.

## Common failures

| Symptom | Row | Cause |
|---------|-----|-------|
| Whole answer appears at once in prod, streams locally | 2 | proxy or CDN buffering, or compression middleware on the stream route |
| Long turns cut off at 10 s / 60 s / 300 s | 3 | serverless `maxDuration` or proxy idle timeout below the turn |
| Threads gone after deploy; "snapshot not found" on resume | 1 | in-memory checkpointer or storage in prod |
| Works locally, tool says unauthenticated in prod | 5 | auth header not forwarded by the runtime, or env set only on the web app |
| Provider outage takes the assistant down | 6 | no fallback in the target env |
