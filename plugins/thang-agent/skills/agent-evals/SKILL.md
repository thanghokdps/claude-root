---
model: opus
effort: high
name: agent-evals
description: Builds the test and eval layers of an LLM agent — scripted fake chat models for unit tests, LLM-judged eval suites with baselines and a CI gate, and a model-comparison matrix of quality, cost, latency and refusals. Use when adding tests or evals to an agent, an eval suite passes without running anything, or choosing or changing the model or provider an agent uses.
when_to_use: write evals for the agent, eval suite, LLM judge, baseline regression, CI eval gate, scripted fake model, "test agent không cần gọi model thật", compare models, switch to a cheaper model, model refuses or behaves differently after a model change
---

# agent-evals

**Invoke:** `/agent-evals [unit | suite | compare-models] <behaviour or candidate models>`

Unit tests prove code paths with no model. Evals prove behaviour with a real model. Keep them in separate trees and separate commands; never let evals run inside `test`.

---

## Mode unit — no real model

- Scripted chat model returning a fixed sequence of messages and tool calls; failing model for the error paths. Use the framework's fakes or the repo's existing helpers before writing new ones.
- Fakes for upstream adapters and the pending-action store; a real local database where the repo supports one.
- Must-have assertions: routing per rule · tool args from trusted context · no write before confirm · error → short answer · recursion/timeout → readable turn.

**Done when:** the new behaviour has a red-then-green unit test, and the suite runs in the repo's normal test command.

## Mode suite — real model, judged

- Layout: an eval tree beside `test/`, its own config and script; credentials read outside the production env.
- Skip a case when credentials are missing **and** fail the run when zero cases executed — a green run that ran nothing is a lie.
- Case id `<file>::<name>` is the baseline key; renames are declared, not silent.
- Deterministic checks first (tool chosen, args, data written); an LLM judge only for qualities code cannot check, with the median of N samples and a judge model different from the agent model.
- Thresholds per scorer (data integrity at 1.0); assert on outcomes, never exact wording.
- CI gate: path-filtered PRs plus a schedule; fail on missing keys, zero executed, or any case going passed → failed against the last good baseline; privacy-scan the report before publishing it.

**Done when:** the suite runs locally, the gate fails on a deliberately broken case, and the report is published only after the privacy scan.

## Mode compare-models — before changing a model

1. Fix the case set (the suite above) and the candidates (model × provider × options such as reasoning effort).
2. Run every candidate on the same cases; record per candidate: pass rate per scorer, refusals, tool-call accuracy, tokens and cost per turn, latency to first token, provider errors.
3. Check option compatibility (for example reasoning options with bound tools) on each candidate.

| Candidate | Pass % | Refusals | Tool accuracy | Cost/turn | TTFT p50/p95 | Errors |
|---|---|---|---|---|---|---|

**Done when:** the table is filled from real runs and a recommendation names the winner per role (router, answerer, summary), with the cases it loses.
