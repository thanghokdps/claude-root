---
model: opus
effort: high
name: agent-architect
description: Chooses and records the architecture of an AI assistant built on Mastra, LangChainJS or LangGraph with CopilotKit / AG-UI. It runs a one-question-at-a-time architecture interview for a new assistant, or a stock-versus-custom audit of an existing one, then scaffolds the chosen shape from the vendor's official reference repo. Use when starting, initing or scaffolding an AI assistant or chatbot codebase (also with no features yet, or with only Langfuse or LangSmith tracing named), adding a new assistant product, choosing a framework (Mastra, createAgent or StateGraph), or asking whether custom agent code can be replaced by stock.
when_to_use: new AI assistant or chatbot, "I want to build an assistant that helps …", "build a chatbot for our customers / support team", "tôi muốn làm một chatbot / trợ lý AI", described in plain words with no command, "chọn kiến trúc agent", "Mastra hay LangChain", "createAgent hay StateGraph", "custom graph hay agent dựng sẵn", scaffold a CopilotKit + LangGraph or Mastra app, "init codebase chatbot assistant empty features using langchain / mastra / custom langgraph, tracing with langfuse", new chatbot repo on any agent framework with Langfuse or LangSmith tracing, skeleton theo repo mẫu chính chủ (ui-dojo, CopilotKit examples), audit an agent repo for custom code that stock now covers, /project-init suggested it
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/scripts/preflight.sh *)
---

# agent-architect

**Invoke:** `/agent-architect [greenfield | skeleton | audit]`

Picking the wrong shape is the most expensive mistake in an assistant: every later skill builds on it. This skill makes that choice explicit, writes it down, and only then scaffolds.

Rules that apply throughout: `${CLAUDE_PLUGIN_ROOT}/rules/agent-stock-first.md` (the ladder) and `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md` — read both before the first step.

---

## Step 0 — Preflight (blank machine)

Run `bash ${CLAUDE_SKILL_DIR}/scripts/preflight.sh .` and show its table. It checks git, Node ≥ 20, a package manager, a model key (presence only) and a git repo, with the install command for this OS.

- Anything `MISSING` → show it in the table with what it blocks, and go straight on to the interview: the turn ends on the P1 question (skeleton: on the scaffold, or on Q-F when no framework is named), never on a setup question. A turn that ends on a question carries no setup notice: no install command, no `.env` step, no key warning, since the user's answer would be read as answering it. A missing model key or git repo blocks only scaffolding and Step 4's real turn. Give the install commands and ask about installs once the interview is done; never run one without a yes, since installing system software is the user's call.
- Never ask for the key's value in chat; it goes in `.env`, which stays gitignored. The secret guard blocks you from creating or reading `.env`: before the real turn, ask the user to run `! cp .env.example .env` and fill the key.

**Done when:** `missing: 0`, or each missing item is accepted with what it blocks.

## Step 1 — Detect (silent)

Run the detection in `${CLAUDE_SKILL_DIR}/references/shapes.md`. Read `docs/adr/*agent-architecture*` if it exists, and the kickoff doc set if it exists (`docs/kickoff.md`, `docs/requirements.md`, `docs/prerequisites.md`, `docs/stack.md`, `docs/erd.md`, `docs/adr/*`, `docs/api/*`).

- No doc set, no code, and the user mentions documents they have (PRD, ERD, tech stack) → offer `/kickoff` first, so the interview starts from them.

- No agent code yet, and the request sets up, inits or scaffolds a chatbot without saying what it should do (a skeleton, an empty chatbot, "no features yet", only a stack) → **skeleton** (Step 2s).
- No agent code yet, and the request describes what the assistant helps with → **greenfield** (Step 2).
- Agent code exists → **audit** (Step 3).
- An ADR exists and the user did not ask to revisit → report the recorded card and stop.

**Done when:** the `Shape: … · host: … · transport: …` line is written, from grep evidence. With no agent code it reads `Shape: none · host: none · transport: none`, even when the request names a stack: greenfield quotes the named stack in the user's words, with no shape letter, runtime or adapter, and sets shape, host and transport on the defaults card after the problem questions; skeleton maps it at Step 2s.

## Step 2 — Greenfield interview

Pre-fill every answer the kickoff doc set holds (`interview.md` § From the kickoff doc set); ask only what is still open. Ask only the rows `interview.md` § Asked or defaulted marks as asked: the problem (P1–P4) before any technology, then Q-F (only when no stack is named) and Q4 (writes). Q-D is never asked: a Figma link or mockup the user gives is used, and with none the chat is CopilotKit's stock `CopilotChat` with theme tokens, shown on the card. Every other question is defaulted from the doc set, the repo, the request or the recommendation, and shown on **one** defaults card the user accepts or changes.

- **One question per turn, as choices**: `AskUserQuestion` with 2–4 options, the recommended one first with `(Recommended)`, per `interview.md` § Shape of each question; numbered options when the tool is absent. Never a prose question the user must answer in free text. Skip what the repo or the request already answers.
- **Viewports are always set** (Q2v) for any web client, even when every frame is desktop-sized: defaulted to phone (375px) plus desktop and shown on the card.
- **Layout is defaulted, never silent**: single app (L1) or monorepo on pnpm + Turborepo (L2), per `${CLAUDE_SKILL_DIR}/references/layouts.md`, chosen from the clients and deploy answers and shown on the card.
- The shape follows Q-F (`shapes.md` § Framework). A named stack is used as given: Mastra → **M**, LangChain or plain LangGraph → **A** (`createAgent` runs on the LangGraph runtime), custom graph or `StateGraph` → **B**/hybrid. With no stack named, recommend **A** (createAgent + middleware + CopilotRuntime v2), unless the host is edge/Workers or a contract the runtime cannot express forces **B**. Use the decision rule in `shapes.md` for single agent vs supervisor in every framework.
- Every non-L0 choice names its rung and its reason (`${CLAUDE_SKILL_DIR}/references/stock-map.md`).

**Done when:** P1–P4, Q-F and Q4 are answered, and the defaults card (Q1–Q9, Q2v, Q-L, Q-T, Q-D) is accepted or its changed rows answered; anything deferred is recorded with a risk.

## Step 2s — Skeleton (empty chatbot on the named stack)

The user wants the frame of a chatbot on their stack, running and able to chat, and nothing else: no tools, no features, no domain data. Read `${CLAUDE_SKILL_DIR}/references/skeleton.md` first; it holds the recognition rule, the stack map, the defaults card, the done checklist and the closing message.

1. **Recognise it** (`skeleton.md` § 1): a request to set up, init, dựng or scaffold a chatbot that does not say what it should do ("init chatbot empty features", "dựng skeleton chatbot rỗng bằng Next.js + CopilotKit + Mastra", "init chatbot với Next.js và LangGraph"). A request that says what the assistant helps with goes to Step 2.
2. **Map the stack** (`skeleton.md` § 2). Every named piece is a fact, never a question. Plain "LangGraph" or "LangChain" → **A**; "custom graph" or "StateGraph" → **B**; "Mastra" → **M**. Write the shape line and the reference row.
3. **Ask only when no stack is named** (`skeleton.md` § 3): then the framework, and the frontend and database, as `AskUserQuestion` choices. With a stack named, ask nothing. Never ask P1–P4, Q4, Q-D, auth, host, clients or layout, and never ask to accept the card.
4. **Show the defaults card** (`skeleton.md` § 3) as information, and **write a short ADR** (`docs/adr/<NNNN>-agent-architecture.md`): the shape line, the named stack, the reference row, the card, and a *Deferred* section listing P2–P4 and Q4 as "to `/agent-feature`". No Problem section and no Step 2b grill.

**Done when:** the shape line and the reference row are written, every stack piece is named or defaulted, and the ADR is on disk. Then Step 4s, in the same turn.

## Step 2b — Grill the card

Before writing the ADR, check the draft card against the points below. Ask only about **Coverage** gaps and **Writes** — one question per turn, as `AskUserQuestion` options (the fix you recommend first, then e.g. "record as a risk"). **Failure** and **Scope** are written onto the card as risks and boundary rules for the user to read on the ADR confirm, not asked one by one:

- **Coverage** — name each P2 task and ask which agent and tool answers it; a task with no owner is a gap, not a detail.
- **Writes** — for each P3 write: what happens on a wrong target, a double submit, a cancel? Points to Q4's HITL answer.
- **Failure** — per decision: "what breaks first if this is wrong, and how would you notice?" Vague → one hard push, then record it as a risk in the ADR.
- **Scope** — a P4 out-of-scope request: show the boundary rule that refuses it.

Stop when the user confirms the card or every open point is a recorded risk. Then write `docs/adr/<NNNN>-agent-architecture.md` (the next free number; `0001` in a repo with no ADRs) from the template in `interview.md`, the Problem section included.

## Step 3 — Audit (brownfield)

Follow `${CLAUDE_SKILL_DIR}/references/audit.md`. Report only — no migration in this pass.

**Done when:** every concern in the sweep has a row with a verdict, and every "replace candidate" names its parity test.

Offer to record the keeps and the chosen direction as an ADR.

## Step 4 — Scaffold (greenfield, on request)

Build the smallest working slice of the chosen shape, test first where practical:

0. Skeleton mirrored from the official reference row for the card (`${CLAUDE_SKILL_DIR}/references/reference-repos.md`): resolve its SHA now, mirror the **core** only, and add a satellite only when the ADR answer it names asks for it. Place it in the chosen layout (`layouts.md` L1 or L2) with the app tree from `${CLAUDE_PLUGIN_ROOT}/rules/agent-code-structure.md`: `git init`, package manager, TypeScript strict, test runner with its `include` set to the Q-T test location, ESLint, Prettier + `format:check`, path alias, `styles/tokens.css`, `.env.example`. Resolve every version at scaffold time and pin it exactly.
1. Env schema that fails at boot on missing or inconsistent config. If the app stores data and there is no ERD (or the user asks for one from the design), write `docs/erd.md` first per `${CLAUDE_SKILL_DIR}/references/data-model.md`, then the DB schema, first migration and owner-scoped repositories from it through `/db-change` (backend, if installed).
2. Identity: verify the token at the edge → server-injected claims → a trusted-context reader for tools (`contextSchema` → `runtime.context`; a `createAgent` graph on `langgraphjs dev` gets an empty context, so `configurable` per `${CLAUDE_PLUGIN_ROOT}/rules/langgraph.md` § Run context; or Mastra `requestContext` with `MASTRA_RESOURCE_ID_KEY`), with a test that a tool sees the caller's id through the AG-UI adapter; token in request scope only.
3. One agent registered under one agent id (backend registry or the Mastra `agents` map, `langgraph.json` if used, client `agent` prop), its prompt opening with P1.
4. Model factory with three roles, `MODEL_PRIMARY`, `MODEL_FALLBACK` and `MODEL_CHEAP`, named per `${CLAUDE_SKILL_DIR}/references/model-choice.md`: the tier follows the hardest P2 task, volume and budget; exact names are resolved from the provider at setup and written with a cost line into `.env.example` and ADR Q7.
5. Tracing switch with masking on (`${CLAUDE_PLUGIN_ROOT}/rules/agent-tracing-privacy.md`).
6. Exact pins and a single copy of the framework core (`@langchain/core` or `@mastra/core`) (`${CLAUDE_PLUGIN_ROOT}/rules/agent-deps-pinning.md`).
7. One read tool for the first P2 task, against its P3 system, through `/agent-tool` (from the user's API spec when one was given, its Step 0); then one real streamed turn with that task's example message through `/agent-verify-turn`.
8. The P2 example messages as the first eval cases (`/agent-evals`).

Apply `${CLAUDE_SKILL_DIR}/references/optimisation.md` as defaults, not as later work: nostream helper nodes (Mastra: `generate()` helpers, `lastMessages`, `maxSteps`), stable prompt prefix, kill switch per tool. Build in the scaffold rows of `${CLAUDE_SKILL_DIR}/references/production.md` (durable state, health, env forwarding, fallback, masked tracing).

"Implement all" or "don't ask me again" means: take the recommended option at every remaining question and record it as *defaulted* — it never means skipping a skill. After this first slice, every further feature goes through `/agent-feature` (one at a time, each with its reuse inventory and duplicate check), the chat UI through `/agent-design-ui`, and each feature's Done-when is met before the next starts.

Then `/project-init` writes the project's `.claude/` docs, test strategy and `CLAUDE.md` from the scaffold just built, so later sessions and `/agent-feature` read them instead of rescanning.

**Done when:** format, typecheck, lint and tests pass, one real turn streams end to end with its evidence shown, and `/project-init` has written `CLAUDE.md` and `.claude/docs/index.md`.

## Step 4s — Skeleton scaffold (after Step 2s)

Step 4's rules hold (reference repo mirrored at a resolved SHA, core only, exact pins, test first where practical, `optimisation.md` and `production.md` scaffold rows), but build only these, in order:

0. **Project shell** from the Step 2s reference row, in the chosen layout: `git init`, the named package manager, TypeScript strict, test runner on the Q-T location, ESLint, Prettier + `format:check`, path alias, `styles/tokens.css`, `.env.example`.
1. **Env schema** that fails at boot on missing config. A named database gets its client, its connection variable and the migration setup; tables only for what Q5 auth and Q6 history need. No ERD and no domain tables.
2. **Identity** as Step 4 item 2, on the named auth or the dev user (`skeleton.md` § 4), with its test that the agent's trusted context carries the caller's id.
3. **One agent** under the id `assistant`, with **no tools**: its prompt opens with P1, says it has no tools yet, and refuses anything that needs data or actions (`skeleton.md` § 4).
4. **Model factory**: `MODEL_PRIMARY`, `MODEL_FALLBACK`, `MODEL_CHEAP` per `model-choice.md`, sized for general chat; names and a cost line in `.env.example` and ADR Q7.
5. **Tracing switch** with masking on.
6. **Pins**: exact versions, one copy of the framework core.
7. **One chat page**: CopilotKit's stock `CopilotChat` wired to the agent id, styled by theme tokens only, checked at the Q2v viewports. A given design goes to `/agent-design-ui` after this step; no design means the stock chat stays, unasked.
8. **Proof**: one real streamed turn with "hello" through `/agent-verify-turn`, its stream evidence shown, and one smoke eval case (the greeting gets a streamed answer) through `/agent-evals`.

Never in skeleton mode: a tool (backend or frontend), a HITL confirm, a domain table or ERD, a RAG index, a second agent or a router, a feature screen. Each is a feature and goes through `/agent-feature`.

End with the closing message in `skeleton.md` § 6: the stack built, the run command, and **Next features** as sentences to give `/agent-feature`. Switching framework later follows `skeleton.md` § 7.

**Done when:** every box in `skeleton.md` § 5 is ticked with its evidence (the last one is `/project-init`), and the closing message is in the reply.

---

## Hand-offs

Scaffold or skeleton done → `/project-init` → `/verify-done` → `/review-checklist` → `/finish-branch` (ship, if installed). Release → `/release-checklist` with `production.md` (ship, if installed). The remaining P2 tasks, and every later feature → `/agent-feature` · tools → `/agent-tool` · writes → `/agent-hitl` · more agents or routing → `/agent-graph` · web client → `/agent-frontend` · chat UI from a design → `/agent-design-ui` · evals → `/agent-evals` · documents, embeddings or semantic memory → `/agent-rag` · threat model → `/agent-security`.
