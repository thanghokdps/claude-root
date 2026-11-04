---
paths:
  - "**/*.{ts,tsx,mts}"
---

# Chat threads (the sidebar)

Checked on 2026-11-04 against @copilotkit/runtime and @copilotkit/react-core 1.83.0, @ag-ui/langgraph 0.0.45, @langchain/langgraph-api 1.5.7, @langchain/langgraph-sdk 1.12.10, @mastra/core 1.82.0 and @mastra/memory 1.41.0. Run live on a LangGraph server with a fake model, in a browser. The Mastra store calls ran against `InMemoryStore` with a mock model; the Mastra routes and the Mastra web client were not run.

Every chat lists the caller's threads in a sidebar: new chat, switch, delete. The list and the history come from the framework's store, through routes on the framework's own server.

## Why not stock `useThreads`

- Without CopilotKit Intelligence, `GET /threads` reads `runtime.runner.listThreads`, and the default runner is `InMemoryAgentRunner`: the list is gone on restart (1.83.0 `dist/v2/runtime/handlers/intelligence/threads.mjs:110`).
- Rename, archive and delete need Intelligence, a hosted service (same file, `requireIntelligenceRuntime`).
- `connect` replays that same in-memory runner, so `CopilotChat` shows nothing for a thread the runner has not seen (`runner/in-memory.mjs`, `connect`). The server must return the history itself.
- Use `useThreads` only when the project runs Intelligence. An audit must not flag the routes below as custom code stock covers.

## The routes

Three routes, all behind the same caller check as the chat route. The path is `app-threads`, because `threads` is the runtime's own.

| Route                                 | Answers                                                                      |
| ------------------------------------- | ---------------------------------------------------------------------------- |
| `GET <base>/app-threads`              | the caller's threads, newest first: `{ id, title, updatedAt }`, at most 50   |
| `GET <base>/app-threads/:id/messages` | the thread's messages as AG-UI messages; 404 when the caller does not own it |
| `DELETE <base>/app-threads/:id`       | 204; 404 when the caller does not own it                                     |

- The caller comes from the verified token, never from a query string, a body or a client-sent `resourceId`. Another caller's thread answers 404, not 403.
- Never call the store from the browser. The Dojo's `client.listMemoryThreads({ resourceId })` takes the owner from the client, which is safe only in a demo.

## Shapes A and B (LangGraph server)

- Answer the routes inside `hooks.onRequest` of `createCopilotHonoHandler`, after the 401 guard: `throw Response.json(…)`. Throwing a `Response` from this hook is the documented early exit (1.83.0 `dist/v2/runtime/core/hooks.d.mts`, `onRequest`), it runs before routing, and the response keeps its CORS headers (`core/fetch-handler.mjs:96-102,219`). `http.app` takes one Hono app, and `hono` stays out of `package.json`, so a second app is not an option.
- Put them in `server/threads.ts`. It calls `new Client({ apiUrl, defaultHeaders })` from `@langchain/langgraph-sdk` with the headers the route's `headerFactory` sends, so the LangGraph auth user is the caller. The `auth.on("threads", …)` filter (`rules/langgraph.md` § Run context) then scopes `client.threads.search`, `getState` and `delete` by owner. Never filter owners by hand.
- The title is the thread's first `human` message, cut to 60 characters, read from `thread.values.messages` in the search result — when the search carries values. After Stop it does not: the client's Stop calls `runs.cancel` (@ag-ui/langgraph `abortRun`), the server aborts the run as `interrupt` and leaves the thread `idle` (@langchain/langgraph-api 1.5.7 `dist/storage/ops.mjs:1124,1144-1160`), the queue drops the run's checkpoint (`dist/queue.mjs:117`) and `threads.setStatus` writes `thread.values = undefined` (`queue.mjs:150`, `storage/ops.mjs:602-603`) while the checkpoints stay. So the route reads `client.threads.getState(id)` (`values.messages`) for a thread the search lists without values, and drops only a thread with no human message in either — a thread the user stopped keeps its row. Dropping on the search's `values` alone made every stopped thread vanish from the sidebar (found 2026-11-04).
- `human` maps to `user` and `ai` to `assistant`, keeping the message `id`, so `prepareStream` does not append them again. The first tool brings `tool` messages and assistant `toolCalls` into this mapping.
- `langgraph dev` keeps threads in `.langgraph_api/`, which survives a restart and belongs in `.gitignore`. Production needs the checkpointer of `production.md` row 1.

## Shape M (Mastra)

- `registerApiRoute` routes beside `registerCopilotKit` in `server.apiRoutes`, in `src/mastra/routes/threads.ts`. The caller is `c.get("requestContext").get(MASTRA_RESOURCE_ID_KEY)`, set by the middleware of `rules/mastra.md` § identity.
- The agent needs `memory: new Memory()` and the Mastra instance needs `storage`, with `InMemoryStore` from `@mastra/core/storage` as the _dev only_ default.
- From `const memory = await mastra.getAgent(AGENT_ID).getMemory()`: `memory.listThreads({ filter: { resourceId } })` returns `{ threads, total, page, perPage, hasMore }`; `memory.recall({ threadId, resourceId })` returns `{ messages }` and throws when the thread is another resource's, which the route maps to 404; `memory.deleteThread(id)` runs only after `memory.getThreadById({ threadId })` shows `resourceId` is the caller's, since it takes no owner.
- Mastra refuses a run on another resource's thread: `Thread "x" belongs to resource "alice" but resource "bob" was provided`.
- A stored message's text is in `message.content.content`.
- `thread.title` starts empty. Turn it on with `memory: new Memory({ options: { generateTitle: { model } } })` on the cheap model, one extra model call per new thread; the sidebar shows "New chat" until it lands.

## The web client

```tsx
const { agent } = useAgent({ agentId: AGENT_ID });
useEffect(() => {
  let cancelled = false;
  agent.setMessages([]);
  fetchHistory(threadId).then((history) => {
    if (!cancelled) agent.setMessages(history);
  });
  const { unsubscribe } = agent.subscribe({ onRunFinalized: refetchThreads });
  return () => {
    cancelled = true;
    unsubscribe();
  };
}, [agent, threadId]);

return <CopilotChat agentId={AGENT_ID} threadId={threadId} />;
```

- `useAgent` with no `threadId` returns the agent `CopilotChat` drives. `useAgent({ threadId })` throws without `runtimeAgentId`, and a per-thread local `agentId` crashes `CopilotChat` on the next switch: `Agent 'chat-…' not found after runtime sync`.
- New chat is `crypto.randomUUID()`: the LangGraph server answers 400 to any other id. The row appears after the first run, never as an empty row.
- The thread id lives in the route (`/:threadId?`, as the Dojo's `pages/assistant-ui` does), so a reload stays on the thread.
- Deleting the active thread opens a new chat.
- **Stop** (the chat's own button: @copilotkit/react-core 1.84.0 `stopAgent`, else `agent.abortRun()`) cancels the run on the server and ends the stream. The thread stays `idle` with its checkpoints: the next send continues it, a reload shows its stored messages, and the partial answer the user watched is not stored. The list refetches after Stop as after any run (`onRunFinalized`), and the row stays because the list route falls back to the state. There is no separate reset button: New chat starts a fresh thread, Delete removes one, a stopped thread is continued or deleted.
- **New chat, switch or delete while a run streams** stops that run first (`agent.abortRun()` before `agent.setMessages([])`), or the old run's events land in the new thread's view. Send stays disabled while a run streams; the server runs one run per thread.
- The sidebar is a `nav` with a label, the active row carries `aria-current="page"`, each delete button names its thread, and it has loading, empty and error states. At the narrow viewport it becomes a drawer and the composer stays pinned (`agent-design-ui` `chat-states.md`).

## Tests

- Routes: no caller → 401 with CORS headers; a second caller's list is empty, and their read and delete of the first caller's thread → 404; the first caller's read → 200; the first caller's delete → 204, gone from the list; a thread the search lists without `values` (stopped) is listed with its title from the state, and a thread with no human message anywhere is not.
- Web: switching threads shows only that thread's messages; a slow history response from the previous thread is ignored; new chat or switch during a run aborts the run first.
- Live, every row with the console clean, shown as a table in the report: **new chat** → an empty chat, no row until the first answer, then the row with the title, active · **switch** back and forth between two threads → only that thread's messages · **delete** the active thread → a new chat opens; delete another → the active one stays · **Stop mid-answer** → the row stays in the list, the next send on the same thread answers, a reload shows the stored messages without the partial answer · **Stop on a new thread's first answer** → the row appears with the question as its title, the next send answers · **new chat or switch while a run streams** → the old run stops and none of its text lands in the new view · **send while a run streams** → not possible (Stop is in the send button's place) · **reload mid-answer** → the run finishes on the server; the answer shows after switching away and back · **restart the agent server** → both threads still list and open, and a follow-up in a restored thread leaves each message once in the store · **empty list, loading, error** → their states render. Each row is run before the sidebar is called done; a row that cannot run is `not verified: <why>`, never left out.
