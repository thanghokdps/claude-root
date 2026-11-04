---
paths:
  - "**/*.{ts,tsx,mts}"
---

# Chat threads (the sidebar)

Checked against @copilotkit/runtime and @copilotkit/react-core 1.84.1, @ag-ui/langgraph 0.0.45, @ag-ui/mastra 2.0.2, @langchain/langgraph-api 1.5.7, @langchain/langgraph-sdk 1.12.10, @mastra/core 1.82.0, @mastra/memory 1.41.0 and mastra 1.38.0 on 2026-11-05. Run live with a fake streaming OpenAI server behind `OPENAI_BASE_URL`, in a browser, on 2026-11-05: Stop, reload, switch, restart and second caller on a kit skeleton (shape A, `langgraphjs dev` 1.5.7) on 1.84.1; routes, web client, Stop, reload, switch, delete and second caller on `mastra dev` 1.38.0 with `InMemoryStore`.

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
- The title is the thread's first `human` message, cut to 60 characters, read from `thread.values.messages` in the search result — when the search carries values. After a cancelled run it does not: the runtime's runner calls the adapter's `abortRun` (@copilotkit/runtime 1.83.0 `dist/v2/runtime/runner/in-memory.mjs` `stop()`), @ag-ui/langgraph's `abortRun` calls `runs.cancel`, the server aborts the run as `interrupt` and leaves the thread `idle` (@langchain/langgraph-api 1.5.7 `dist/storage/ops.mjs:1124,1144-1160`), the queue drops the run's checkpoint (`dist/queue.mjs:117`) and `threads.setStatus` writes `thread.values = undefined` (`queue.mjs:150`, `storage/ops.mjs:602-603`) while the checkpoints stay — and a thread whose first run is still going has no `values` yet either. So the route reads `client.threads.getState(id)` (`values.messages`) for a thread the search lists without values — the first checkpoint already holds the human message — and drops only a thread with no human message in either. Dropping on the search's `values` alone hid every stopped thread from the sidebar (reproduced 2026-11-04: Stop on a new thread's first answer, the row never appeared, not even after a reload, until the next send).
- `human` maps to `user` and `ai` to `assistant`, keeping the message `id`, so `prepareStream` does not append them again. The first tool brings `tool` messages and assistant `toolCalls` into this mapping.
- `langgraph dev` keeps threads in `.langgraph_api/`, which survives a restart and belongs in `.gitignore`. Production needs the checkpointer of `production.md` row 1.
- **The server keeps a stopped answer.** A cancelled run's checkpoint has no partial answer, so a `MiddlewareFunction` from `@ag-ui/client` on the agent collects the stream and stores it. Never take this text from the browser: a client that can write assistant text forges the history. `rxjs` becomes a direct dependency, pinned to the version `@ag-ui/client` uses.

```ts
// src/<agent folder>/server/keep-stopped-answer.ts
export function keepStoppedAnswer(save: SaveStoppedAnswer): MiddlewareFunction {
  return (input, next) => {
    let open: { id: string; text: string } | null = null;
    return next.run(input).pipe(
      concatMap(async (event): Promise<BaseEvent[]> => {
        if (event.type === EventType.TEXT_MESSAGE_START) {
          open = { id: (event as TextMessageStartEvent).messageId, text: "" };
        } else if (event.type === EventType.TEXT_MESSAGE_CONTENT && open) {
          open.text += (event as TextMessageContentEvent).delta;
        } else if (event.type === EventType.TEXT_MESSAGE_END) {
          open = null;
        } else if (event.type === EventType.RUN_FINISHED && open) {
          const stopped = open;
          open = null;
          await save(input.threadId, stopped.id, stopped.text);
          return [
            {
              type: EventType.TEXT_MESSAGE_END,
              messageId: stopped.id,
            } as BaseEvent,
            event,
          ];
        }
        return [event];
      }),
      concatMap((events) => events),
    );
  };
}
```

- Attach it with `new LangGraphAgent({ … }).use(keepStoppedAnswer(save))`; `clone()` carries middlewares (@ag-ui/client 1.0.2). `save` calls the caller's threads client, `updateState(threadId, { values: { messages: [{ id, type: "ai", content: text }] }, asNode: "model_request" })`, so the owner filter still applies. On shape B name the graph's own model node. The added `TEXT_MESSAGE_END` also ends the server's `Cannot send 'RUN_FINISHED' while text messages are still active`; it lands after the snapshot, so the web guard below still applies.

## Shape M (Mastra)

- `registerApiRoute` routes beside `registerCopilotKit` in `server.apiRoutes`, in `src/mastra/routes/threads.ts`. The caller is `c.get("requestContext").get(MASTRA_RESOURCE_ID_KEY)`, set by the middleware of `rules/mastra.md` § identity.
- The agent needs `memory: new Memory()` and the Mastra instance needs `storage`, with `InMemoryStore` from `@mastra/core/storage` as the _dev only_ default.
- From `const memory = await mastra.getAgent(AGENT_ID).getMemory()`: `memory.listThreads({ filter: { resourceId } })` returns `{ threads, total, page, perPage, hasMore }`; `memory.recall({ threadId, resourceId })` returns `{ messages }` and throws when the thread is another resource's, which the route maps to 404; `memory.deleteThread(id)` runs only after `memory.getThreadById({ threadId })` shows `resourceId` is the caller's, since it takes no owner.
- Mastra refuses a run on another resource's thread: `Thread "x" belongs to resource "alice" but resource "bob" was provided`.
- A stored message's text is in `message.content.content`.
- `thread.title` starts empty. Turn it on with `memory: new Memory({ options: { generateTitle: { model } } })` on the cheap model, one extra model call per new thread; the sidebar shows "New chat" until it lands.
- Pass `identifyUser` to `registerCopilotKit`: its extra options go to `CopilotRuntime`, and without it the runtime logs `Listing and clearing threads need a caller identity` and answers 403 on its own `GET /threads`. It receives the `Request`, not the Hono context, so it verifies the token itself instead of reading `requestContext`.
- **Stop keeps the partial answer with no extra code**: the adapter aborts the model call, no snapshot follows, and Mastra stores the words streamed so far, so the middleware and the snapshot guard of shapes A and B are not needed here. That stored message gets a new id, while a completed answer keeps its stream id (@ag-ui/mastra 2.0.2, @mastra/core 1.82.0). `connect` replays the stopped run under the stream id, so an id merge shows that answer twice after a switch. Use this `apply` merge on shape M; a beyond-history answer is dropped only before the first new user message, so a repeated answer in a new turn stays:

```ts
const known = new Set(history.map((m) => m.id));
const stored = new Set(
  history.filter((m) => m.role === "assistant").map((m) => m.content),
);
let newTurn = false;
const beyond = agent.messages.filter((m) => {
  if (known.has(m.id)) return false;
  newTurn ||= m.role === "user";
  return newTurn || !stored.has(m.content);
});
const merged = [...history, ...beyond];
```

- `InMemoryStore` loses every thread on a restart, so the restart row of § Tests applies once a durable store is wired.

## The web client

```tsx
const { agent } = useAgent({ agentId: AGENT_ID });
useEffect(() => {
  let cancelled = false;
  let history: Message[] | null = null;
  let streaming: string | null = null;
  // History order first; what the agent holds beyond it (a question just sent, an answer streaming in) follows.
  const apply = () => {
    if (cancelled || !history) return;
    const known = new Set(history.map((m) => m.id));
    const merged = [
      ...history,
      ...agent.messages.filter((m) => !known.has(m.id)),
    ];
    if (!sameIds(merged, agent.messages)) agent.setMessages(merged);
  };
  agent.setMessages([]);
  fetchHistory(threadId).then((loaded) => {
    history = loaded;
    apply();
  });
  const { unsubscribe } = agent.subscribe({
    onTextMessageStartEvent: ({ event }) => {
      streaming = event.messageId;
    },
    onTextMessageEndEvent: () => {
      streaming = null;
    },
    // A stopped run ends on a checkpoint snapshot without the half-streamed answer: keep what the user read.
    onMessagesSnapshotEvent: ({ event }) =>
      streaming && !event.messages.some((m) => m.id === streaming)
        ? { stopPropagation: true }
        : undefined,
    onRunFinalized: () => {
      streaming = null;
      refetchThreads();
    },
    onMessagesChanged: apply,
  });
  return () => {
    cancelled = true;
    unsubscribe();
  };
}, [agent, threadId]);

return <CopilotChat agentId={AGENT_ID} threadId={threadId} />;
```

- `useAgent` with no `threadId` returns the agent `CopilotChat` drives. `useAgent({ threadId })` throws without `runtimeAgentId`, and a per-thread local `agentId` crashes `CopilotChat` on the next switch: `Agent 'chat-…' not found after runtime sync`.
- New chat is `crypto.randomUUID()`: the LangGraph server answers 400 to any other id. The row appears once the first message is stored (during the first answer), never as an empty row. New chat navigates with router state (`{ fresh: true }`) and the page skips the history fetch for it: fetching a thread that does not exist yet is a 404 the browser logs as an error, three times under StrictMode, and the console is never clean. That state lives in `history.state` and survives a reload, so clear it on mount or a reloaded new chat skips its history and, once `connect` has nothing to replay (a restarted server), sits on "Loading conversation": `useEffect(() => { if (fresh) window.history.replaceState({ ...window.history.state, usr: null }, ""); }, [fresh]);`.
- The thread id lives in the route (`/:threadId?`, as the Dojo's `pages/assistant-ui` does), so a reload stays on the thread.
- Deleting the active thread opens a new chat.
- **`connect` replays, out of order.** `CopilotChat` calls `connect` for the thread the page loaded on, and the runtime answers with its in-memory snapshot of the runs this process served for it (`runner/in-memory.mjs` `connect()`); a run still streaming resumes in the chat after a reload. That snapshot lands before or after the history route's messages and, merged by id, puts the replayed runs ahead of the earlier ones (observed: a thread's third exchange shown first after a reload, the first two after it). The sync above keeps the server's order and re-applies it on `onMessagesChanged`; it is idempotent, so no loop.
- **Stop** (the chat's own button, in the send button's place while a run streams) aborts the browser's request. Whether the server's run is cancelled too depends on the runtime (observed on @copilotkit/runtime 1.83.0, in-memory runner, 2026-11-04): a thread the page loaded on (`connect`ed) runs to completion, the full answer is stored while the user saw a partial one, and it shows after a reload; a thread opened by in-app navigation gets `POST /threads/<id>/runs/<id>/cancel?action=interrupt`, the run ends `interrupted`, none of the answer is stored, and the next send continues the thread. @copilotkit/react-core 1.84.0 adds `stopAgent` → the runtime's `POST agent/<id>/stop/<threadId>`, which cancels in both cases (run on 1.84.1, 2026-11-04: first answer, later answer and after a reload, the model call aborted each time, `interrupted`, the next send continues). A cancelled run ends with `@ag-ui/langgraph`'s `MESSAGES_SNAPSHOT` from the checkpoint, which never held the partial answer, so without the guard above the text leaves the chat at once (1.83.0 and 1.84.1). The guard keeps it on screen and `keepStoppedAnswer` stores it, so it stays after the next answer and a reload. Either way the list refetches (`onRunFinalized` fires on Stop) and the row stays because the list route reads the state. There is no separate reset button: New chat starts a fresh thread, Delete removes one, a stopped thread is continued or deleted.
- **New chat, switch or delete while a run streams** ends the browser's request like Stop does; the old run's text never lands in the new view, and switching back shows whatever the server stored. Nothing to abort by hand.
- The sidebar is a `nav` with a label, the active row carries `aria-current="page"`, each delete button names its thread, and it has loading, empty and error states. At the narrow viewport it becomes a drawer and the composer stays pinned (`agent-design-ui` `chat-states.md`).

## Tests

- Routes: no caller → 401 with CORS headers; a second caller's list is empty, and their read and delete of the first caller's thread → 404; the first caller's read → 200; the first caller's delete → 204, gone from the list; a thread the search lists without `values` (stopped) is listed with its title from the state, and a thread with no human message anywhere is not.
- Web: switching threads shows only that thread's messages; a slow history response from the previous thread is ignored; a `connect` snapshot that lands after the history (the last run first, the earlier messages missing) ends up in history order with the streaming message kept after it, an already ordered list triggers no `setMessages`, and a snapshot that lacks a message still streaming is stopped while one after `TEXT_MESSAGE_END` applies; on shape M, a replayed stopped answer is dropped and a repeated answer after a new user message stays.
- Middleware (shapes A and B): a run that ends mid-text calls `save` once with the streamed text and emits `TEXT_MESSAGE_END` before `RUN_FINISHED`; a completed run never calls `save`.
- Live, every row with the console clean (a fake model behind `OPENAI_BASE_URL` that streams slowly makes Stop reproducible without a key), shown as a table in the report: **new chat** → an empty chat, no history request, the row with the title once the first answer starts · **switch** back and forth between two threads → only that thread's messages · **delete** the active thread → a new chat opens; delete another → the active one stays · **Stop mid-answer** → the words already streamed stay on screen, the row stays in the list, the next send on the same thread answers, and the partial answer is still there, in order, after that answer and after a reload · **switch away and back after Stop** → the stopped answer shows once · **Stop on a new thread's first answer** → the row appears with the question as its title, the next send answers · **new chat or switch while a run streams** → none of the old run's text lands in the new view; switching back shows what the server stored · **send while a run streams** → Stop is in the send button's place, and a message typed and entered meanwhile goes out after the answer ends, as its own exchange, never interleaved · **reload mid-answer** on a thread the page loaded on → the answer resumes streaming and the messages stay in order; reload again → still in order · **restart the agent server** → the list shows its error state with Retry while it is down, Retry restores it, both threads still open, every message is stored once (`threads/<id>/state`: distinct ids), and a reload of a thread that began as a new chat shows its messages · **a second caller** → an empty list, 404 on the first caller's thread. Each row is run before the sidebar is called done; a row that cannot run is `not verified: <why>`, never left out.
