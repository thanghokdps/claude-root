---
model: opus
effort: high
name: agent-architect
description: Chooses and records the architecture of an AI assistant built on CopilotKit, AG-UI, LangChainJS or LangGraph — a one-question-at-a-time architecture interview for a new assistant, or a stock-versus-custom audit of an existing one — and scaffolds the chosen shape. Use when starting an AI assistant or chatbot project, adding a new assistant product, or asking which agent architecture, createAgent or StateGraph, or whether custom agent code can be replaced by stock middleware.
when_to_use: new AI assistant or chatbot, "chọn kiến trúc agent", "createAgent hay StateGraph", "custom graph hay agent dựng sẵn", scaffold a CopilotKit + LangGraph app, audit an agent repo for custom code that stock now covers, /project-init suggested it
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

Walk `${CLAUDE_SKILL_DIR}/references/interview.md` in order: the problem (P1–P4) before any technology, then Q1–Q9 with the design question Q-D and the layout question Q-L after Q2.

- **One question per turn**, each with *Why this matters* and *My recommendation*. Skip what the repo or the request already answers.
- **Layout is asked, never assumed**: single app (L1) or monorepo on pnpm + Turborepo (L2), per `${CLAUDE_SKILL_DIR}/references/layouts.md`. Recommend one from the clients and deploy answers, then wait.
- Default recommendation is shape **A** (createAgent + middleware + CopilotRuntime v2) unless the host is edge/Workers or a contract the runtime cannot express forces **B**; use the decision rule in `shapes.md` for single agent vs supervisor.
- Every non-L0 choice names its rung and its reason (`${CLAUDE_SKILL_DIR}/references/stock-map.md`).

**Done when:** P1–P4, Q-D, Q-L and Q1–Q9 are answered or explicitly deferred with a risk.

## Step 2b — Grill the card

Before writing the ADR, attack the draft card one question per turn until it holds:

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

0. Skeleton of the chosen layout (`layouts.md` L1 or L2): `git init`, package manager, TypeScript strict, test runner, lint, `.env.example`. Resolve every version at scaffold time and pin it exactly.
1. Env schema that fails at boot on missing or inconsistent config.
2. Identity: verify the token at the edge → server-injected claims → a trusted-context reader for tools; token in request scope only.
3. One agent registered under one agent id (backend registry, `langgraph.json` if used, client `agent` prop), its prompt opening with P1.
4. Model factory with fallback; a cheap model for routing/summary.
5. Tracing switch with masking on (`${CLAUDE_PLUGIN_ROOT}/rules/agent-tracing-privacy.md`).
6. Exact pins and a single LangChain copy (`${CLAUDE_PLUGIN_ROOT}/rules/agent-deps-pinning.md`).
7. One read tool for the first P2 task, against its P3 system, through `/agent-tool`; then one real streamed turn with that task's example message through `/agent-verify-turn`.
8. The P2 example messages as the first eval cases (`/agent-evals`).

Apply `${CLAUDE_SKILL_DIR}/references/optimisation.md` as defaults, not as later work: nostream helper nodes, stable prompt prefix, kill switch per tool.

**Done when:** typecheck, lint and tests pass, and one real turn streams end to end with its evidence shown.

---

## Hand-offs

The remaining P2 tasks, and every later feature → `/agent-feature` · tools → `/agent-tool` · writes → `/agent-hitl` · more agents or routing → `/agent-graph` · web client → `/agent-frontend` · chat UI from a design → `/agent-design-ui` · evals → `/agent-evals` · threat model → `/agent-security`.
