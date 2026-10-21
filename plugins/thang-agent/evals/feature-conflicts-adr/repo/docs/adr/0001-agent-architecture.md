# ADR 0001 — Agent architecture
Status: accepted · Date: 2026-09-02

## Problem
Users: shop customers on the web store · Problem: "where is my order" tickets take a day to answer.
| Task (P2) | Example message | Agent | Tool(s) |
|-----------|-----------------|-------|---------|
| Track an order | "Đơn #DH1024 tới đâu rồi?" | orders | getOrder |
| List my orders | "Tôi có đơn nào đang giao?" | orders | listOrders |
Systems (P3): Orders API → read → commerce team · Out of scope (P4): changing, cancelling or paying for orders; refunds — hand off to the support form.
Good answer means: status, carrier and ETA quoted from the API.

## Architecture card
Layout: L1 single app · Shape: A · Host: node · Transport: CopilotRuntime · Clients: web
Agents: orders → order lookup → 2 tools
Writes/HITL: none — read-only assistant · Identity: caller's session token forwarded to the Orders API · Checkpoints: memory · Memory: none
Models: primary sonnet → fallback haiku
Tracing: Langfuse, PII masked · Evals: track + list must pass

## Decisions
| # | Decision | Reason | Ladder rung (L0–L3) |
|---|----------|--------|---------------------|
| 1 | createAgent + toolRetryMiddleware | one loop, read tools only | L1 |
| 2 | no HITL | no writes in scope | L0 |

## Rejected alternatives
Custom StateGraph — nothing a middleware hook cannot do.
## Revisit when
A task needs to write to the Orders API.
