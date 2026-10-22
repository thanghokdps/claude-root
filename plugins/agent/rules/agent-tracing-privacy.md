---
paths:
  - "**/*.{ts,mts}"
---

# Agent tracing and privacy

- One switch selects the tracing provider (`none` | provider names); `none` is a valid production setting and the default in tests.
- Tracing never fails a turn: every exporter call is caught, and flushing happens in `finally` after the callback queue drains.
- Mask by default: drop or hash message text, tool args and tool results unless an explicit setting allows them; user ids are keyed-hashed (HMAC), never raw.
- Secrets, tokens and caller-supplied API keys never reach traces, logs, checkpoints or eval reports.
- Build the trace handler per turn with the turn's ids (thread, run, agent); never share a mutable handler across requests.
- Record per turn: model, provider that answered (after fallback), token usage, latency to first token, tool calls and their status — the inputs for triage and cost.
- Eval reports and CI artifacts pass a privacy scan before they are published.
