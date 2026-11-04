# Input while a confirm card is open

Read by `/agent-hitl` Steps 3–4 and by `/agent-frontend` for the composer. Covers everything the user can do while a card waits: click, type a yes or a no, type a correction, change the subject, wait too long, reload.

Verified against the installed sources on 2026-11-04: `@ag-ui/client` 1.0.2, `@copilotkit/core` and `@copilotkit/react-core` 1.84.0, `@ag-ui/langgraph` 0.0.43, `@langchain/langgraph` 1.6.0, `@langchain/langgraph-api` 1.4.4, `langchain` 1.5.3. Confirm each line on the versions the repo installs before relying on it.

## What the stack does on its own

- A run on a thread with an open interrupt must carry a `resume` entry for every open interrupt id, or `@ag-ui/client` throws before anything is sent (`AbstractAgent.onInitialize`: "Thread has N pending interrupt(s) not addressed by resume"). An expired interrupt is accepted only with status `cancelled`.
- Stock `CopilotChat` send with a backend card open: the typed message is appended locally (`onSubmitInput` → `agent.addMessage`), `RunHandler.runAgent` catches the throw above and emits `AGENT_RUN_FAILED`, nothing reaches the server, the card stays. That is the "I typed and nothing happened" symptom.
- On a resume run the LangGraph server ignores `input` when `command` is set (`@langchain/langgraph-api` `dist/stream.mjs`: `graphInput = kwargs.command != null ? command : input`). A message sent beside the resume never enters the thread; the typed text must travel **in the resume payload**.
- A run through `@ag-ui/langgraph` with open interrupts and no resume re-emits the open interrupts as the run outcome and runs nothing (`prepareStream`, last return): the same card again, the message dropped.
- Only a caller on the LangGraph API itself can send a plain input to an interrupted thread; LangGraph then discards the interrupted task and starts from the input (`dist/pregel/loop.js` `_first`, `discardTasks`). The pending record is orphaned — which is why it carries `expiresAt` and why a thread holds one open action: a new record on the thread supersedes an older pending one.
- `useInterrupt` hides the card when a run starts on the thread (`onRunStartedEvent` → `setPending(null)`) and shows the interrupt that run ended with (`onRunFinalized`). "Close the old card, show the corrected one" is one resume run that ends in a new interrupt; the app never keeps its own copy of the card state.
- `interrupt()` called again in the same tool execution consumes the next resume value (`@langchain/langgraph` `dist/interrupt.js`: `interruptCounter`, `scratchpad.resume[idx]`), so a tool can ask again without a second record.
- A tool may return `Command({ update: { messages } })`; the tool node of `@langchain/langgraph` (`prebuilt/tool_node.js`, `isCommand(output)`) and of `langchain` `createAgent` (`agents/utils.js`) both apply it. That is how the typed line enters the thread history.
- Shape M: `requireApproval` resumes only on `true` / `{ approved: true }`, declines on `{ approved: false }` or a cancelled resume, and fails the run on any other payload (`${CLAUDE_PLUGIN_ROOT}/rules/mastra.md`). A typed reply needs `suspend()` with a `resumeSchema` that has `reply`.

## The matrix

| The user…                                                     | The client sends                                                             | Below the interrupt                                                                                                             | The user sees                                                                                                                                           |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| clicks Confirm                                                | `resume: [{ interruptId, status: "resolved", payload: { approved: true } }]` | claim `pending → applying`, write once, outcome `completed`                                                                     | the result line                                                                                                                                         |
| clicks Cancel or closes the card                              | `status: "cancelled"`                                                        | `cancelled`, nothing written                                                                                                    | "Đã hủy"                                                                                                                                                |
| types a plain yes ("ok", "đồng ý", "ừ lưu đi")                | the message added locally, then `resolved` + `{ reply, messageId }`          | classifier → `approve` → as a click; the typed line appended to the thread                                                      | the result line; the typed line stays after a reload                                                                                                    |
| types a no ("hủy", "thôi", "không")                           | same                                                                         | `cancel` → as a click; typed line appended                                                                                      | "Đã hủy"                                                                                                                                                |
| types a correction ("đổi tên thành Bob", "ok nhưng ngày mai") | same                                                                         | `change` → record `superseded`, nothing written, tool result `re-propose`; the model calls the tool again with corrected fields | the old card gone, a new card with the corrected field, built from a fresh server read                                                                  |
| types about something else                                    | same                                                                         | `other` → `superseded`, nothing written, tool result `answer`                                                                   | the answer, then one line: the pending action closed and was not saved, and the phrase that opens it again                                              |
| types something the classifier cannot place ("?", "hmm")      | same                                                                         | `unclear` → `interrupt()` again with the same fields and `message: "Xác nhận hay hủy?"`; the record stays `pending`             | the same card again                                                                                                                                     |
| waits past `expiresAt`                                        | nothing                                                                      | a resume after `expiresAt` is refused; the record expires                                                                       | the card says it expired and offers only Close (a `cancelled` resume); a Confirm after expiry would be refused by the client and leave the thread stuck |
| reloads the page                                              | `connect`; the card comes back from `pendingInterrupts`                      | —                                                                                                                               | the same card; a reply after the reload follows the rows above                                                                                          |
| sends again while the resume run is in flight                 | queued: one run per thread                                                   | —                                                                                                                               | nothing until that run ends                                                                                                                             |

## Client

- Composer: while `useInterrupt` holds a pending interrupt, submit does `agent.addMessage({ id, role: "user", content: text })` and then `resolve({ reply: text, messageId: id })` instead of `sendMessage`. Wire it through a custom `input` slot of `CopilotChat` (the slot receives `onSubmitMessage`) or the headless composer on `useAgent`. The card's buttons stay `resolve({ approved: true })` and `cancel()`. The reply carries the same message id the client added, so the thread's copy dedupes against the local one.
- The card copy names both ways: "Bấm Xác nhận, hoặc gõ ok / hủy" — in every language the chat supports, from the same `labels` source as the rest of the chat.
- `responseSchema` on the interrupt admits both payloads: `{ approved: boolean }` and `{ reply: string, messageId?: string }`.
- Expiry: the card reads `expiresAt`, shows it, and after it offers only Close; the composer's interception still sends a `cancelled` resume for an expired card before the new message runs as a plain input in a second run.
- Chat channels: a text reply in the thread from the user who asked is the same resume; text from anyone else is ignored (`${CLAUDE_PLUGIN_ROOT}/skills/agent-frontend/references/chat-channels.md`).
- Headless clients do the same with `resume[]`; they never send a plain input while `pendingInterrupts` is non-empty.

## Server, below the interrupt

The record is the source of truth; the decision is stored on it before anything else happens, so a replayed resume returns the stored outcome and never classifies or writes twice.

1. Load the record by the interrupt id. Not `pending` → return its stored outcome. Past `expiresAt` → mark `expired`, write nothing, return the refusal line.
2. `{ approved: true }` → claim `pending → applying`, perform the upstream write, store `completed` (or `not_applied` from the upstream response). `{ approved: false }` or a cancelled resume → `cancelled`.
3. `{ reply, messageId }` → one structured-output model call, then act on the stored class:
   - Input: the card's action type, the fields as the card showed them, the reply. Output: one of `approve | cancel | change | other | unclear`.
   - Rules in that prompt: `approve` only when the whole message is an unconditional yes to exactly this card; a message that adds, changes or questions a field is `change`; a plain no is `cancel`; something about another subject is `other`; anything else is `unclear`. Temperature 0, the ADR's cheap model, a deadline like any tool call; a model error or an output outside the enum is `unclear`.
   - `approve` and `cancel` → as the clicks above.
   - `change` and `other` → store `superseded` with the reply and the class, write nothing, and return `Command({ update: { messages: [toolMessage, humanMessage] } })`: the `ToolMessage` outcome is `{ status: "not_applied", reason: "superseded", reply, next: "re-propose" | "answer" }`, the `HumanMessage` is the reply with `id: messageId`.
   - `unclear` → append the human message the same way, then `interrupt()` again with the same value and a message that asks for a yes or a no; the record stays `pending`. Shape M: `suspend()` again.
   - Every reply branch appends the typed line, so the thread history matches what the user saw.
4. The next interrupt on the thread (the corrected card) is a new record and a new interrupt id; the superseded record is never resumed.

Shape M stores the typed line the way the repo already stores thread messages; confirm the call on the installed `@mastra/memory` before using it.

## Prompt rule for the agent

- A tool result with `next: "re-propose"` → call the same write tool again with the fields the reply corrects, the target unchanged unless the reply names another one; the card is rebuilt from a fresh server read (Step 2). Never say the change happened.
- A tool result with `next: "answer"` → answer the message; end with one line that says the pending `<action>` closed and nothing was saved, and the phrase that opens it again. Derive `<action>` from the tool constants, never type it into the prompt.
- `/agent-evals` keeps a case per row; the row's wording is never asserted, the outcome is.

## Tests (or the live check when tests are declined)

- Typed "ok" and typed "ừ lưu đi" → one upstream write each, the typed line in the thread after a reload.
- "ok nhưng đổi tên thành Bob" → zero writes, the first record `superseded`, a second record `pending` with the corrected field, the stream showing one interrupt outcome per card (`/agent-verify-turn`).
- An unrelated message → zero writes, `superseded`, the answer plus the one-line note.
- "?" → zero writes, the record still `pending`, a second interrupt outcome in the same run.
- The same typed resume replayed → no second classification, no second write.
- An expired card: a typed yes is refused and nothing is written; Close sends `cancelled`.
- The classifier table: at least ten utterances per supported language with the expected class, run as an `/agent-evals` case against the real model; the branch logic above runs under a unit test with the classifier mocked.
