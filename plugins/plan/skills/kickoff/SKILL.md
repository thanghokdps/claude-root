---
model: opus
effort: high
name: kickoff
description: Starts a new project from the documents the team already has. It collects them first (requirements, prerequisites, tech stack, ERD, architecture decisions, design, API specs, non-functional needs, delivery), reads them into one canonical doc set, shows a coverage matrix, and only then grills the user on what is missing, partial or conflicting — until the project is ready to start. Use when starting a new project or product, handing over a PRD, ERD or ADR to begin from, or before /project-init on an empty folder.
when_to_use: new project, start from scratch, "bắt đầu dự án mới", "init dự án", "đây là PRD / requirement / ERD / tech stack", kick off a project from our docs, project intake, "tôi có tài liệu rồi", onboarding a project before any code, empty folder before /project-init
---

# Kickoff

**Invoke:** `/kickoff [paths or links to the docs you have]`

Documents first, questions second. A question whose answer is already written down wastes the user's turn and lets the harness drift from what the team agreed. This skill reads what exists, shows what is covered, and grills only the gaps.

The doc set, its order and its canonical files are in `${CLAUDE_SKILL_DIR}/references/doc-set.md`. Read it before Step 1.

---

## Step 1 — Collect what exists

Scan before asking: `docs/`, `specs/`, `README*`, root `*.md`, `openapi.*` / `swagger.*`, `*.prisma`, Drizzle or SQL schema files, `docs/adr/*`, plus every path or link the user named. Anything found is read now and goes straight to Step 2: the first message to the user is the matrix, and a document the scan did not find is asked for as its ❌ row in Step 4 ("do you have the Stripe spec, or shall we interview?"). Only when the scan finds nothing at all, ask **once**, through `AskUserQuestion`, where the documents are:

- *I'll attach or link them (Recommended)* — paths, URLs, pasted text, a Figma link
- *Some of it, ask me the rest*
- *Nothing written yet — interview me*

Read every source the user gives. A link you cannot open (private Drive, Confluence) → ask for an export or paste; never guess its content. A pasted secret → tell the user to rotate it, and keep only the variable name.

**Done when:** every source is listed with its path or link and whether it was read.

## Step 2 — Read into the doc set, in order

Walk the nine items of `doc-set.md` in order (requirements → prerequisites → stack → data model → architecture → design → external APIs → non-functional → delivery). For each, extract what the sources say into its canonical file.

- Quote the user's sentences verbatim; link the original, which stays where it was. Never paraphrase a requirement into new words.
- A large PRD or ticket set can go through `business-analyst:analyze-specs` (business-analyst, if installed) for acceptance criteria.
- Facts that code or config can answer (an existing `package.json`, a schema file) are read, not asked.
- Name the business domain from the requirements and write `Domain: <name>` into `docs/requirements.md`. Internal HR or workplace tools (time off, approvals, room or meal booking, maintenance requests) are `workplace`; nothing that fits is `general`. Unsure → it is a row to grill, asked as a need ("Is this a tool your own staff use for requests and bookings?").

**Done when:** each item has its canonical file, or is marked absent.

## Step 3 — Coverage matrix

Write `docs/kickoff.md` from the template in `doc-set.md`: one row per sub-item, status ✅ (source `path:line`), ⚠️ partial, ❌ missing, ⛔ conflict (both sources quoted), or n/a (with why: no UI, no stored data). No sub-item is folded into its neighbour: a provider the requirements name is ✅ for *system*, and its *spec or docs* sub-item stays ❌ until a spec sits under `docs/api/` — naming Stripe is not having its API. Show the matrix to the user before the first question.

**Done when:** the matrix is shown, and every mandatory row has a status.

## Step 4 — Grill the gaps only

Order: ⛔ conflicts first (they block the most), then ❌ and ⚠️ rows in doc-set order, because every later item derives from the requirements.

- One question per turn, as `AskUserQuestion` with 2–4 options; the recommended option first with `(Recommended)`, drafted from what the docs already say. Numbered options when the tool is absent.
- Facts you look up, decisions you ask. Never ask about a ✅ row.
- Rows 3, 5, 8 and 9 (stack, architecture, non-functional, delivery) are asked as needs, never as tools, per `${CLAUDE_PLUGIN_ROOT}/references/need-questions.md`; the canonical file records the tech with the need it came from.
- A weak answer ("later", "should be fine") gets one hard push, then is recorded as a decision with its risk.
- "Use your recommendation" for the rest → take the recommended option at each remaining row, list them in one message, and mark them *defaulted* in the matrix.
- After each answer, update the canonical file and the matrix row.

**Done when:** no row is ❌ or ⛔ without a recorded decision, deferral or risk.

## Step 5 — Readiness gate

Ready when every mandatory row is ✅, *defaulted*, or deferred with what it blocks. Close `docs/kickoff.md` with:

- **Open risks** — every deferral and pushed-back answer, one line each.
- **Start here** — the next skill and why (Step 6).

**Done when:** the gate holds and the user has seen the closing summary.

## Step 6 — Hand off

No code is written here.

- `Domain: workplace` → the workplace pack turns on in this repo from the next session (core's repo-profile hook); its `/workplace-review` (workplace, if installed) and its domain questions apply from then on. Say so in the closing summary.
- AI assistant or chatbot → `/agent-architect greenfield` (ai, if installed). It reads this doc set and asks only what is still open.
- Other app with an open approach → `/brainstorming`. Approach already decided → `/writing-plans`, wave 1 = scaffold.
- Code already exists → `/project-init` (core, if installed), which reads this doc set into `.claude/docs/`.
