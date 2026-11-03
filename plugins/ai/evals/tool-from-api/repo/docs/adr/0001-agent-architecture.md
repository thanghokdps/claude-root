# ADR 0001 — Agent architecture
Status: accepted · Date: 2026-10-20

## Problem
Users: shop customers on the web store · Problem: order questions and cancellations wait a day for support.
| Task (P2) | Example message | Agent | Tool(s) |
|-----------|-----------------|-------|---------|
| Track an order | "Đơn #DH1024 tới đâu rồi?" | orders | from the Orders API |
| Cancel an open order | "Huỷ đơn #DH1024 giúp tôi" | orders | from the Orders API |
Systems (P3): Orders API → read + cancel → commerce team · Out of scope (P4): payments, refunds, admin operations.
Good answer means: status quoted from the API; a cancel happens only after the customer confirms.

## Architecture card
Layout: L1 single app · Shape: A · Host: langgraph · Transport: CopilotRuntime · Clients: web
Agents: orders → order questions → tools not built yet (to come from the Orders API through /agent-tool)
Writes/HITL: cancel needs a confirm card · Identity: caller's session token forwarded to the Orders API · Checkpoints: memory · Memory: none
Models: primary sonnet → fallback haiku
Tracing: none · Evals: track + cancel must pass

## Decisions
| # | Decision | Reason | Ladder rung (L0–L3) |
|---|----------|--------|---------------------|
| 1 | createAgent on the LangGraph server | one loop, a few tools | L1 |

## Revisit when
A task needs a second agent.
