# 0003 — Opus decides, Sonnet writes code, Haiku does mechanical work

**Status:** Accepted (27 Oct 2026)

## Context

Running every step on the strongest model is expensive; running decisions on a cheap model makes wrong calls that cost more than the tokens saved.

## Decision

- The main session (Opus) plans, decides and reviews.
- Work it hands to a subagent runs on the cheapest model that can do it: `sonnet` for code from an approved plan, `haiku` for mechanical work and searches.
- A skill whose wrong call is expensive (plans, architecture, review, security, migrations, root cause) pins `model: opus`. A light skill (`/btw`, `/compact`, `/verify-done`, `/create-pr`, …) sets no model and runs on the session's model.
- A subagent stuck twice on the same check goes back to Opus to re-plan; never a third try on the same brief.

## Consequences

- Code is written by Sonnet and reviewed by Opus; `ticket-gate` checks that a cheaper subagent wrote a ticket's code.
- The brief to a cheaper model must leave nothing to decide: files, contract, the test to pass, the done check.
- The user naming a model overrides the table.

## Where

`plugins/core/rules/model-cost.md`, skill frontmatter `model:`, `plugins/dev/hooks/ticket-gate.sh`.
