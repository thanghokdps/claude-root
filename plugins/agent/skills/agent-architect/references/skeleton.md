# Skeleton mode — an empty chatbot on the user's stack

Read with Step 2s and Step 4s of `SKILL.md`. The user wants a chatbot that runs, streams one answer and has no features yet. Every feature comes later, one at a time, through `/agent-feature`.

## 1. Recognise it

Skeleton mode applies when the request sets up, inits, dựng or scaffolds a chatbot without saying what it should do: a skeleton, an empty chatbot, a shell, "no features yet", or only a stack. Examples: "init chatbot empty features", "init chatbot với Next.js và LangGraph", "dựng skeleton chatbot", "chưa làm feature nào", "khung trống", "just the skeleton", "empty chatbot on <stack>".

A request that describes what the assistant helps with ("…hỗ trợ khách tra cứu đơn hàng") is greenfield (Step 2): the full interview and plan run there. Do not ask which mode; the wording decides.

## 2. Map the named stack (never re-ask a named piece)

| The user says | Shape | Reference row (`reference-repos.md`) | Framework core (one copy) |
|---|---|---|---|
| "LangChain", "createAgent", or "LangGraph" with no custom graph mentioned | **A** | R4 (L1) · R6 (L2 monorepo) | `@langchain/core`, `@langchain/langgraph`, `langchain` |
| "custom LangGraph graph", "StateGraph", or a Workers/edge host | **B** | R5 agent + R7 emitter | `@langchain/core`, `@langchain/langgraph` |
| "Mastra" | **M** | R2 (in-process CopilotKit) · R1 (own Mastra server) | `@mastra/core` |
| no stack named at all | ask the stack, see § 3 | — | — |

- Plain "LangGraph" means shape A: `createAgent` runs on the LangGraph runtime. If the user then mentions fixed steps, an edge host or their own graph, switch to B and say why in one line.
- **Frontend:** Next.js App Router by default. Another named React app (Vite, React Router) keeps its own setup, with the CopilotKit runtime in a small Node server.
- **Chat UI:** stock `CopilotChat` (v2) with theme tokens. A design link is noted on the card for `/agent-design-ui` later; nothing is built from it now.
- **Database / ORM:** use the named one (Postgres + Drizzle, Prisma, SQLAlchemy, SQLite). None named → no database. Add one only when Q6 keeps durable chat history, and say so on the card.
- **Auth:** use the named one (Better Auth, Clerk, NextAuth, the company SSO). None named → not asked: a fixed dev user behind a flag (`DEV_USER_ID`, refused when `NODE_ENV=production`), read through the same trusted-context reader a real login will fill. Shown on the card; real auth comes later as a feature.
- **Package manager, host, layout:** use the named ones. Otherwise use the defaults from `layouts.md` and Q1, shown on the card.

Speak only the chosen framework from here on (`shapes.md`).

## 3. Questions and the card

- **The request names a stack** (any framework, or a frontend with an agent framework): ask nothing. Build on it, and default every piece it leaves open.
- **The request names no stack at all** ("init chatbot empty features"): ask the stack once, in at most two `AskUserQuestion` turns, the recommended option first:
  1. Framework (Q-F): *LangChain `createAgent` (Recommended)* / *Mastra* / *custom LangGraph graph*.
  2. Frontend and database in one question: *Next.js, no database (Recommended)* / *Next.js + Postgres + Drizzle* / *another stack (type it)*.
- Never ask P1–P4, Q4, Q-D, auth, host, clients or layout, and never ask the user to accept the card. P1 is "A general chat assistant".

Show the card below in the reply as information, then build. The user changes a row later by saying so.

| Row | Skeleton default |
|---|---|
| P1 purpose | "A general chat assistant" |
| Q1 host · Q2 clients · Q-L layout | Node on the framework's own server · web · L1 single app unless a monorepo is named |
| Q5 identity | the named auth, else the dev user above |
| Q-D design | a link given in the request, else stock `CopilotChat` with theme tokens |
| Q3 agent shape | one agent, id `assistant` |
| Q4 writes · P2–P4 | deferred to `/agent-feature` |
| Q6 memory | thread history in the framework's store (Mastra `storage`, LangGraph checkpointer). Postgres when one is named, in-memory otherwise, marked *dev only* |
| Q7 models | mid tier for `MODEL_PRIMARY`, smallest tier for `MODEL_CHEAP`, next tier down for `MODEL_FALLBACK`; names resolved from the provider, with a cost line at 20 turns/day per user. Marked *revisit when the first feature lands* |
| Q8 tracing | the switch, off by default, masking on |
| Q9 evals | one smoke case |
| Q2v viewports · Q-T tests | 375 px + desktop · tests beside the file |

## 4. What gets built

`SKILL.md` Step 4s, with these readings:

- **Step 2, identity.** There are no tools yet, so the test proves the agent's trusted context carries the caller's id. It calls the runtime with a signed-in user and asserts that the context reader returns that id. The first tool's test will reuse that reader.
- **Step 3, agent.** One agent registered under `assistant`. Its prompt holds P1, one line saying it has no tools yet and answers from general knowledge, and the refusal line "I can't do that yet" for anything that needs data or actions.
- **Database.** Only the connection, the migration tooling and, when Q6 keeps history, the conversation tables. No ERD and no domain tables.

Not built: tools, HITL, RAG, feature screens, design work and domain data.

## 5. Done when (show each with its evidence)

- [ ] `format:check`, typecheck, lint and tests pass (paste the command output)
- [ ] the app boots with `.env` filled from `.env.example`, and fails with a clear message when a required var is missing
- [ ] `/agent-verify-turn` with "hello" streams a real answer end to end (AG-UI events shown)
- [ ] the chat page renders that answer at 375 px and at desktop width
- [ ] `docs/adr/<NNNN>-agent-architecture.md` lists the stack, the card and the deferred rows
- [ ] the smoke eval passes
- [ ] `/project-init` wrote `CLAUDE.md` and `.claude/docs/` from the skeleton (show `ls .claude/docs`)

## 6. The closing message

End with exactly this shape, so the next step is copy-paste:

```markdown
Skeleton ready — <framework> · <frontend> · <db or "no DB"> · <auth>. Run: `<dev command>`.

Next, one at a time (each goes through /agent-feature):
1. "<the user's first likely task as a sentence>"
2. "<…>"
Design for the chat: give the Figma link and say "làm UI chat theo figma này".
```

When P1 gives no hint of tasks, list three generic starters: a read tool on their main data, a confirm-before-write action, and the chat design.

## 7. Changing the framework later

- **Skeleton with no features yet:** rebuild the skeleton on the new framework. Delete the old agent folder, re-run Step 4, and write a new ADR that supersedes the old one. This is cheaper than migrating, and nothing of the user's is lost.
- **Once features exist:** this is a migration, not a swap. Run Step 3 (audit), record the switch in a new ADR, and move one feature at a time with its tests kept green. A stored-data change in that move goes through `/write-migration`.
