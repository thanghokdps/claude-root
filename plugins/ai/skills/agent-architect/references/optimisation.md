# Optimisation and rollout checklist

Measure first: per-turn tracing (tokens, latency to first token, provider that answered, tool calls) plus the eval baseline. Change one thing, re-measure.

## Latency
- Stream only the answering node; router, prepare and summary nodes run `nostream`.
- A small, fast model for router, summary, titles and suggestions; the strong model only where answers are written.
- Independent read tools run as parallel tool calls.
- Checkpoint durability `exit` (one write per turn) unless mid-run recovery is required.
- Suggestions and titles run off the turn's critical path, failing open.

## Tokens and cost
- Static instructions first, dynamic context last — a stable prefix stays cache-friendly.
- `summarizationMiddleware` with an explicit trigger and keep window; `contextEditingMiddleware` for old tool output.
- Fewer, sharper tools; descriptions in short bullets.
- Do not stream state the client never reads (`STATE_SNAPSHOT`, `RAW`).
- Call limits per run and per thread.

## Reliability
- Fallback last in the middleware chain; non-retryable errors (400/422) never fall back.
- Retry reads only; mutations never.
- Recursion limit and timeout land as a readable turn.
- Memory, tracing and suggestions never fail a turn.

## Rollout safety
- Every tool and every agent can be switched off by config without a deploy (kill switch), defaulting to on only after its evals pass.
- Prompt and scope changes ship behind the eval gate; risky ones run in shadow (log the new routing, serve the old) before switching.
- Model or provider changes go through `agent-evals` compare-models before they reach the default.
- Pinned agent-stack bumps travel alone, with a real streamed turn as evidence.
- Before release: `production.md` (durable state, streaming, time limits, health, env, fallback, tracing, rollback).

## Shape M (Mastra) equivalents

The lists above name LangChain / LangGraph pieces. In Mastra (names checked against mastra.ai docs on 2026-10-23; confirm on the installed `@mastra/core`):

| LangChain / LangGraph | Mastra |
|-----------------------|--------|
| `nostream` helper nodes | helper calls (router, titles, summary) use `agent.generate()`; only the answering agent is streamed |
| `summarizationMiddleware` keep window | `new Memory({ options: { lastMessages: N } })` — an explicit window, set on purpose rather than left at the default; `observationalMemory` when old turns must be compressed rather than dropped |
| token budget on the prompt | `new TokenLimiterProcessor({ limit, trimMode: 'contiguous' })` from `@mastra/core/processors` in `inputProcessors`; in `outputProcessors` it caps the answer |
| `contextEditingMiddleware` for old tool output | `ToolCallFilter` in `inputProcessors` — drops tool calls from the model input, memory keeps them |
| recursion limit / call limits per run | `maxSteps` per `generate()` / `stream()` call, or once in the agent's `defaultOptions`; with a supervisor, on every call |
| retry and fallback middleware | default error processors (e.g. `StreamErrorRetryProcessor`) retry transient stream failures — check they never replay a write; fallback per `${CLAUDE_PLUGIN_ROOT}/rules/mastra.md` |
