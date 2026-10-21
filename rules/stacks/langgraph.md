---
paths:
  - "**/*.{ts,tsx,mts}"
  - "**/langgraph.json"
---

# LangGraph rules (TypeScript)

## State

- Reducer channels (`messages`) **append**: a node returns only the delta, never the concatenated history.
- A node returns `Partial<State>` with only the fields it changes; clear a field explicitly (`field: null`), never by omission.
- Keep state small and serialisable — it is checkpointed every turn. Large or rotating values (tokens, clients, adapters) go in `configurable` or request scope, never in state.
- Values written once at graph entry (identity, model choice) are never mutated by later nodes.

```typescript
return { messages: [aiResponse] };                    // delta — correct
return { messages: [...state.messages, aiResponse] }; // duplicates history
```

## Graph lifecycle

- Compile once at module level with its dependencies; invoke many times. Never compile or build a checkpointer per request.
- Pass per-run limits at invoke time: `recursionLimit`, timeout, abort `signal`.
- `GraphRecursionError` and timeouts end as a readable assistant turn, never a 500.
- Nodes that route, prepare or summarise must not stream into the chat: tag them `nostream` / disable message emission.

## Models

- `temperature: 0` for anything that routes or produces structured output.
- Check model-specific options against the bound tools (some models reject reasoning-effort with tools); verify on the installed model, not from memory.

## Streaming

- `streamEvents(input, { version: "v2" })` — always v2.

## Interrupts

- `interrupt()` needs a checkpointer and a stable `thread_id`; resume with `new Command({ resume })` on the same thread.
- Code above `interrupt()` re-runs on resume: make it idempotent. The only write allowed above it is the pending-action record (see `agent-identity-and-tools.md`).
- Code below `interrupt()` runs once, after the decision — that is where the real write happens.
- Never retry a node or tool that can raise `GraphInterrupt`; rethrow it from every wrapper.
