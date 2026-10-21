---
model: opus
effort: high
name: agent-security
description: Threat-models an LLM agent — prompt injection through tool results, shared context and memory, tool authority and confused-deputy risks, data exfiltration through rendered output, secrets and PII in traces, and mapping agent controls to compliance evidence such as SOC 2. Use when an agent gains a new tool, data source or client, before an agent ships, or when asked whether an agent meets a compliance control.
when_to_use: prompt injection, agent threat model, "agent có an toàn không", SOC 2 for the agent, PII masking in tracing, can the model be tricked into acting for another user, encrypting agent data at rest, compliance evidence for an AI feature
---

# agent-security

**Invoke:** `/agent-security [scope: whole agent | <tool, source or client>]`

Complements the built-in `/security-review` (code-level vulnerabilities in a diff). This skill asks what the *model* can be made to do.

---

## Step 1 — Inventory (facts)

List from the code:

| Asset | Entry | Who controls the text | Reaches the model as | Can trigger |
|---|---|---|---|---|

Rows: user messages, tool results (each upstream), shared client context, long-term memory, retrieved documents, file/image inputs, system prompt, chat-channel messages from others.

**Done when:** every tool and every context source is a row.

## Step 2 — Threats per row

- **Injection**: text from a row the user does not control instructs the model ("ignore previous…", hidden markup). Mitigation: treat as data in a delimited block, never as instructions; the tools it could trigger still need trusted identity and HITL.
- **Confused deputy**: the model acts with the server's or another user's authority. Check `rules/stacks/agent-identity-and-tools.md` — no identity in tool args, permission per resource, server-resolved targets.
- **Unconfirmed writes**: any mutation reachable without the HITL gate (`/agent-hitl`).
- **Exfiltration**: rendered markdown links/images, tool calls to arbitrary URLs, data from one user's context shown to another (shared threads, caches, memory keyed wrongly).
- **Leakage**: secrets or tokens in state, checkpoints, traces, logs or eval reports; PII in traces without masking (`agent-tracing-privacy.md`).
- **Abuse and cost**: unbounded loops, oversized inputs, missing rate limits after auth, missing call limits.

**Done when:** every row has each applicable threat marked mitigated (with file:line) or open.

## Step 3 — Prove the risky ones

For each open or doubtful threat, a test or an eval case that attempts it: an injected tool result, a prompt naming another user, a forged context key, a link-rendering payload. Use `/agent-evals` for model-dependent cases.

**Done when:** every high-risk threat has a test or eval that fails without the mitigation.

## Step 4 — Compliance mapping (when asked)

Map each control to evidence in the repo:

| Control | Mechanism | Evidence (file, test, config) | Gap |
|---|---|---|---|

Typical rows: access control (verified identity, per-resource checks), change management (eval gate, pinned deps), confidentiality (masking, encryption at rest, retention), logging (masked traces, audit records of tool calls), incident response (kill switch per tool).

**Done when:** each control has evidence or a named gap; write the summary in the language the reader asked for.

Code-level findings go to `/security-review`; hard-gate findings block the change until fixed.
