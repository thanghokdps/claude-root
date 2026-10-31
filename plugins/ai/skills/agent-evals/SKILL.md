---
model: opus
effort: high
name: agent-evals
description: Builds the test, eval and observability layers of an LLM agent — scripted fake chat models for unit tests, an eval dataset, LLM-judged eval suites with baselines and a CI gate, tracing wired into an existing agent, and a model-comparison matrix of quality, cost, latency and refusals. Use when adding tests, an eval dataset or tracing to an agent, an eval suite passes without running anything, or choosing or changing the model or provider an agent uses.
when_to_use: write evals for the agent, eval dataset, golden cases, evaluate the agent prompt, LLM judge, baseline regression, CI eval gate, scripted fake model, "test agent không cần gọi model thật", set up Langfuse or LangSmith tracing, observability for the agent, compare models, switch to a cheaper model, model refuses or behaves differently after a model change
---

# agent-evals

**Invoke:** `/agent-evals [unit | dataset | suite | observability | compare-models] <behaviour or candidate models>`

Unit tests prove code paths with no model. Evals prove behaviour with a real model. Keep them in separate trees and separate commands; never let evals run inside `test`.

**Precondition.** No assistant in the repo yet (no agent framework dependency, no agent entry point, no ADR) → stop and say so: a new assistant starts with `/agent-architect`, which writes the ADR this skill builds inside. Never scaffold an agent here to have something to test; come back once the ADR exists.

---

## Mode unit — no real model

- Scripted chat model returning a fixed sequence of messages and tool calls; failing model for the error paths. Use the framework's fakes or the repo's existing helpers before writing new ones.
- Fakes for upstream adapters and the pending-action store; a real local database where the repo supports one.
- Must-have assertions: routing per rule · tool args from trusted context · no write before confirm · error → short answer · recursion/timeout → readable turn.

**Done when:** the new behaviour has a red-then-green unit test, and the suite runs in the repo's normal test command.

## Mode dataset — the cases every suite runs on

- One file per behaviour in `evals/datasets/<behaviour>.jsonl`; each line `{ id, input, context, expected: { agent, tool, args, outcome }, tags, fixture? }`. `context` is the trusted identity and page state the turn would have; `tool: null` means no tool may be called; `fixture` stubs a tool's upstream result (used for injection cases). Copy the shape from `${CLAUDE_SKILL_DIR}/references/dataset-example.jsonl` (happy path, missing argument, authorisation, write + confirm, injection, routing regression).
- The suite reads these files; `expected.tool` / `args` / `agent` are deterministic checks, `outcome` is the judge's rubric.
- Sources, in order: the ADR's example messages, bugs already fixed (one case each, tagged `regression`), masked production traces, then synthetic variants (paraphrase, other language, missing field) generated from those and reviewed by a person.
- Cover per tool: happy path, ambiguous target, missing argument, out-of-scope request, prompt injection inside a tool result; per write: confirm and cancel.
- No raw PII or secrets; production-derived cases pass the privacy scan before they are committed.

**Done when:** every tool and every routing rule has at least one case, and every fixed bug has a `regression` case.

## Mode suite — real model, judged

- Layout: an eval tree beside `test/`, its own config and script; credentials read outside the production env.
- Skip a case when credentials are missing **and** fail the run when zero cases executed — a green run that ran nothing is a lie.
- Case id `<file>::<name>` is the baseline key; renames are declared, not silent.
- Deterministic checks first (tool chosen, args, data written); an LLM judge only for qualities code cannot check, with the median of N samples and a judge model different from the agent model.
- Thresholds per scorer (data integrity at 1.0); assert on outcomes, never exact wording.
- RAG answers: retrieval recall@k on the expected `sourceId` (no LLM, cheap) plus faithfulness and citation scorers, and a "not found" answer for out-of-corpus cases (`/agent-rag` Step 6).
- CI gate: path-filtered PRs plus a schedule; fail on missing keys, zero executed, or any case going passed → failed against the last good baseline; privacy-scan the report before publishing it. `.github/workflows/**` is a guarded path (core's `sensitive-path` blocks the write): write the workflow to `evals/ci/<name>.yml`, show it, and ask the user to move it, or hand it to `/pipeline` (devops, if installed). Never report the gate as done when the file was blocked.

**Done when:** the suite runs locally, the gate fails on a deliberately broken case, and the report is published only after the privacy scan.

## Mode observability — tracing in an existing agent

Follow `${CLAUDE_PLUGIN_ROOT}/rules/agent-tracing-privacy.md`. A new assistant gets this from `/agent-architect`.

1. Add the switch (`TRACING_PROVIDER=none|langfuse|langsmith`) and the provider's keys to `.env.example` as names only; `none` in tests.
2. Build the callback handler per turn with thread, run and agent ids; mask message text, tool args and results by default; HMAC the user id.
3. Record per turn: model, answering provider, tokens, latency to first token, tool calls and status. Flush in `finally`; an exporter error never fails the turn.
4. Tag traces with the prompt version, so a bad answer maps back to a prompt and a dataset case.

**Done when:** one real turn shows up in the provider with masked content and the fields above, and the same turn with `TRACING_PROVIDER=none` still answers.

## Mode compare-models — before changing a model

1. Fix the case set (the suite above) and the candidates (model × provider × options such as reasoning effort).
2. Run every candidate on the same cases; record per candidate: pass rate per scorer, refusals, tool-call accuracy, tokens and cost per turn, latency to first token, provider errors.
3. Check option compatibility (for example reasoning options with bound tools) on each candidate.

| Candidate | Pass % | Refusals | Tool accuracy | Cost/turn | TTFT p50/p95 | Errors |
|---|---|---|---|---|---|---|

**Done when:** the table is filled from real runs and a recommendation names the winner per role (router, answerer, summary), with the cases it loses.
