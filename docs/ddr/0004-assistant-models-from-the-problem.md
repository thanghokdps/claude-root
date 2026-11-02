# 0004 — An assistant's models come from its hardest task, volume and budget

**Status:** Accepted (27 Oct 2026)

## Context

A kit that names one model for every assistant is wrong for most of them: a FAQ bot and a multi-step planning agent need different tiers, and model names and prices change every few months.

## Decision

`/agent-architect` never picks a model from habit. Three roles are set in `.env` (`MODEL_PRIMARY`, `MODEL_FALLBACK`, `MODEL_CHEAP`). The primary tier comes from the difficulty of the hardest task (light / medium / heavy), checked against volume (turns per day) and the stated budget, with a monthly cost line in the ADR. Exact names are resolved at setup from the provider's current list. A change of model goes through the `/agent-evals` comparison matrix, not by editing the name.

## Consequences

- The ADR shows why a model was chosen and what it costs per month.
- The cheapest tier that passes the must-pass evals wins; the eval judge is never the primary model.

## Where

`plugins/agent/skills/agent-architect/references/model-choice.md`, `/agent-evals compare-models`.
