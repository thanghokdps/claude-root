# Model choice — from the problem to exact model names

The ADR names exact models (Q7), but never from habit. The names come out of three inputs, and a cost line shows the reasoning.

## Inputs (from the interview, never asked again)

| Input | Read from | Values |
|---|---|---|
| Difficulty of the hardest P2 task | P2 examples | **light**: answer from given context, one tool call · **medium**: 2–4 tool calls, choose between tools, short reasoning · **heavy**: multi-step plans, long documents, code, money or legal consequences |
| Volume | P1 users × expected turns per user per day (default 20) | turns/day |
| Budget | kickoff docs, or the user's answer on the defaults card | USD/month cap, or "none stated" |

## Roles

Every assistant has three model roles, set in `.env` and read by `models.ts`:

- `MODEL_PRIMARY` answers the user. Use the cheapest tier that passes the must-pass evals (Q9) for the hardest task.
- `MODEL_FALLBACK` serves rate limits and outages. Use the next tier down from the same provider; another provider only when the user names a second one. A key that happens to be set in the shell never adds a provider.
- `MODEL_CHEAP` runs background jobs where quality barely matters: chat titles, routing, summaries and the eval judge. Use the provider's smallest tier. The judge must not be the primary model.

The provider is OpenAI unless the user names another. It is never inferred from which key is set: two runs on one machine must not pick two providers.

## Tier rule

| Hardest task | Primary tier |
|---|---|
| light | small |
| medium | mid |
| heavy | top |

Then apply the budget. Estimate `cost/month = turns/day × 30 × (input tokens × input price + output tokens × output price)`. Use 3k input tokens and 400 output tokens per turn unless the repo's traces show real numbers. When the estimate is over the budget, step the primary down one tier and record the risk. Never step down silently.

## Exact names

The tiers resolve to names at setup, not from memory. List the models the key can use with the provider's models endpoint, and take each tier's current model and price from the provider's pricing page. Write the names into `.env.example` and the ADR (Q7), together with the cost line:

`Q7 — primary <name> (tier, why), fallback <name>, cheap <name>; ≈ $<n>/month at <turns>/day (<in>/<out> tokens per turn).`

The models that resolved on 27 Oct 2026 (OpenAI re-checked against the models endpoint and developers.openai.com/api/docs/pricing on 3 Nov 2026), as a starting point to verify:

| Tier | OpenAI | Anthropic |
|---|---|---|
| top | `gpt-5.5` ($5.00 / $30.00 per 1M in/out) | `claude-opus-5-5` |
| mid | `gpt-5.4-mini` ($0.75 / $4.50) | `claude-sonnet-5-5` |
| small | `gpt-5.4-nano` ($0.20 / $1.25); `gpt-5-nano` ($0.05 / $0.40) is the older, cheaper option for `MODEL_CHEAP` | `claude-haiku-5-5` |

## Changing later

Change a model only with numbers. `/agent-evals` builds the model-comparison matrix (quality, cost, latency and refusals per model) on the must-pass evals. A swap that keeps the evals green and lowers cost goes in as an ADR change entry.
