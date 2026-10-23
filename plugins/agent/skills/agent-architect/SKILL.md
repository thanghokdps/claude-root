---
model: opus
effort: high
name: agent-architect
description: Chooses and records the architecture of an AI assistant built on Mastra, LangChainJS or LangGraph with CopilotKit / AG-UI. It runs a one-question-at-a-time architecture interview for a new assistant, or a stock-versus-custom audit of an existing one, then scaffolds the chosen shape from the vendor's official reference repo. Use when starting an AI assistant or chatbot project, adding a new assistant product, choosing a framework (Mastra, createAgent or StateGraph), or asking whether custom agent code can be replaced by stock.
when_to_use: new AI assistant or chatbot, "chọn kiến trúc agent", "Mastra hay LangChain", "createAgent hay StateGraph", "custom graph hay agent dựng sẵn", scaffold a CopilotKit + LangGraph or Mastra app, skeleton theo repo mẫu chính chủ (ui-dojo, CopilotKit examples), audit an agent repo for custom code that stock now covers, /project-init suggested it
allowed-tools: Bash(bash ${CLAUDE_SKILL_DIR}/scripts/preflight.sh *)
---

# agent-architect

**Invoke:** `/agent-architect [greenfield | audit]`

Picking the wrong shape is the most expensive mistake in an assistant: every later skill builds on it. This skill makes that choice explicit, writes it down, and only then scaffolds.

Rules that apply throughout: `${CLAUDE_PLUGIN_ROOT}/rules/agent-stock-first.md` (the ladder) and `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md` — read both before the first step.

---

## Step 0 — Preflight (blank machine)

Run `bash ${CLAUDE_SKILL_DIR}/scripts/preflight.sh .` and show its table. It checks git, Node ≥ 20, a package manager, a model key (presence only) and a git repo, with the install command for this OS.

- Anything `MISSING` → list it with the printed command and ask before running any install; installing system software is the user's call. A missing model key blocks only Step 4's real turn — the interview can go on.
- Never ask for the key's value in chat; it goes in `.env`, which stays gitignored.

**Done when:** `missing: 0`, or each missing item is accepted with what it blocks.

## Step 1 — Detect (silent)

Run the detection in `${CLAUDE_SKILL_DIR}/references/shapes.md`. Read `docs/adr/*agent-architecture*` if it exists.

- No agent code yet → **greenfield** (Step 2).
- Agent code exists → **audit** (Step 3).
- An ADR exists and the user did not ask to revisit → report the recorded card and stop.

**Done when:** the `Shape: … · host: … · transport: …` line is written, from grep evidence.

## Step 2 — Greenfield interview

Walk `${CLAUDE_SKILL_DIR}/references/interview.md` in order: the problem (P1–P4) before any technology, then Q-F (framework; skipped when the stack is named), then Q1–Q9 with the design question Q-D and the layout question Q-L after Q2.

- **One question per turn, as choices**: `AskUserQuestion` with 2–4 options, the recommended one first with `(Recommended)`, per `interview.md` § Shape of each question; numbered options when the tool is absent. Never a prose question the user must answer in free text. Skip what the repo or the request already answers.
- **Viewports are asked** (Q2v) for any web client, even when every frame is desktop-sized.
- **Layout is asked, never assumed**: single app (L1) or monorepo on pnpm + Turborepo (L2), per `${CLAUDE_SKILL_DIR}/references/layouts.md`. Recommend one from the clients and deploy answers, then wait.
- The shape follows Q-F (`shapes.md` § Framework). A named stack is used as given: Mastra → **M**, LangChain → **A**, custom graph → **B**/hybrid. With no stack named, recommend **A** (createAgent + middleware + CopilotRuntime v2), unless the host is edge/Workers or a contract the runtime cannot express forces **B**. Use the decision rule in `shapes.md` for single agent vs supervisor in every framework.
- Every non-L0 choice names its rung and its reason (`${CLAUDE_SKILL_DIR}/references/stock-map.md`).

**Done when:** P1–P4, Q-F, Q-D, Q-L, Q-T (no tests yet), Q1–Q9 and Q2v (web) are answered, defaulted to the recommendation, or explicitly deferred with a risk.

## Step 2b — Grill the card

Before writing the ADR, attack the draft card one question per turn until it holds — each as `AskUserQuestion` options (the fix you recommend first, then the alternatives, e.g. "record as a risk"):

- **Coverage** — name each P2 task and ask which agent and tool answers it; a task with no owner is a gap, not a detail.
- **Writes** — for each P3 write: what happens on a wrong target, a double submit, a cancel? Points to Q4's HITL answer.
- **Failure** — per decision: "what breaks first if this is wrong, and how would you notice?" Vague → one hard push, then record it as a risk in the ADR.
- **Scope** — a P4 out-of-scope request: show the boundary rule that refuses it.

Stop when the user confirms the card or every open point is a recorded risk. Then write `docs/adr/0001-agent-architecture.md` from the template in `interview.md`, the Problem section included.

## Step 3 — Audit (brownfield)

Follow `${CLAUDE_SKILL_DIR}/references/audit.md`. Report only — no migration in this pass.

**Done when:** every concern in the sweep has a row with a verdict, and every "replace candidate" names its parity test.

Offer to record the keeps and the chosen direction as an ADR.

## Step 4 — Scaffold (greenfield, on request)

Build the smallest working slice of the chosen shape, test first where practical:

0. Skeleton mirrored from the official reference row for the card (`${CLAUDE_SKILL_DIR}/references/reference-repos.md`): resolve its SHA now, mirror the **core** only, and add a satellite only when the ADR answer it names asks for it. Place it in the chosen layout (`layouts.md` L1 or L2) with the app tree from `${CLAUDE_PLUGIN_ROOT}/rules/agent-code-structure.md`: `git init`, package manager, TypeScript strict, test runner with its `include` set to the Q-T test location, ESLint, Prettier + `format:check`, path alias, `styles/tokens.css`, `.env.example`. Resolve every version at scaffold time and pin it exactly.
1. Env schema that fails at boot on missing or inconsistent config. If the app stores data and there is no ERD (or the user asks for one from the design), write `docs/erd.md` first per `${CLAUDE_SKILL_DIR}/references/data-model.md`, then the DB schema, first migration and owner-scoped repositories from it through `/db-change`.
2. Identity: verify the token at the edge → server-injected claims → a trusted-context reader for tools (`config.configurable`, or Mastra `requestContext` with `MASTRA_RESOURCE_ID_KEY`); token in request scope only.
3. One agent registered under one agent id (backend registry or the Mastra `agents` map, `langgraph.json` if used, client `agent` prop), its prompt opening with P1.
4. Model factory with fallback; a cheap model for routing/summary.
5. Tracing switch with masking on (`${CLAUDE_PLUGIN_ROOT}/rules/agent-tracing-privacy.md`).
6. Exact pins and a single copy of the framework core (`@langchain/core` or `@mastra/core`) (`${CLAUDE_PLUGIN_ROOT}/rules/agent-deps-pinning.md`).
7. One read tool for the first P2 task, against its P3 system, through `/agent-tool` (from the user's API spec when one was given, its Step 0); then one real streamed turn with that task's example message through `/agent-verify-turn`.
8. The P2 example messages as the first eval cases (`/agent-evals`).

Apply `${CLAUDE_SKILL_DIR}/references/optimisation.md` as defaults, not as later work: nostream helper nodes (Mastra: `generate()` helpers, `lastMessages`, `maxSteps`), stable prompt prefix, kill switch per tool. Build in the scaffold rows of `${CLAUDE_SKILL_DIR}/references/production.md` (durable state, health, env forwarding, fallback, masked tracing).

"Implement all" or "don't ask me again" means: take the recommended option at every remaining question and record it as *defaulted* — it never means skipping a skill. After this first slice, every further feature goes through `/agent-feature` (one at a time, each with its reuse inventory and duplicate check), the chat UI through `/agent-design-ui`, and each feature's Done-when is met before the next starts.

Then `/project-init` writes the project's `.claude/` docs and test strategy from the scaffold just built.

**Done when:** format, typecheck, lint and tests pass, and one real turn streams end to end with its evidence shown.

---

## Hand-offs

Scaffold done → `/verify-done` → `/review-checklist` → `/finish-branch`. Release → `/release-checklist` with `production.md`. The remaining P2 tasks, and every later feature → `/agent-feature` · tools → `/agent-tool` · writes → `/agent-hitl` · more agents or routing → `/agent-graph` · web client → `/agent-frontend` · chat UI from a design → `/agent-design-ui` · evals → `/agent-evals` · documents, embeddings or semantic memory → `/agent-rag` · threat model → `/agent-security`.
