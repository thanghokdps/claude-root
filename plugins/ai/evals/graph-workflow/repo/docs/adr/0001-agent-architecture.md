# ADR 0001 — Agent architecture
Status: accepted · Date: 2026-10-20

## Problem
Users: customers of each shop on the platform (one tenant per shop) · Problem: refund and product questions wait a day for support.
| Task (P2) | Example message | Agent | Tool(s) |
|-----------|-----------------|-------|---------|
| Check an order | "Đơn #DH1024 đã giao chưa?" | support | getOrder |
| Refund an order | "Hoàn tiền đơn #DH1024 giúp tôi" | support | issueRefund (after a staff approval) |
| Answer from the product guide | "Máy này sạc bao lâu thì đầy?" | support | planned |
Systems (P3): Orders API → read · Payments API → refund write → finance team · Out of scope (P4): payments other than refunds.
Good answer means: facts quoted from the API or the tenant's own guide; no refund without approval.

## Architecture card
Layout: L1 single app · Shape: M · Host: mastra · Transport: registerCopilotKit · Clients: web
Agents: support → orders and refunds → 2 tools
Writes/HITL: issueRefund needs a staff approval (not built yet) · Identity: tenantId and userId from the verified session, set in requestContext by the server · Memory: none
Models: primary sonnet → fallback haiku
Tracing: none · Evals: check + refund must pass

## Decisions
| # | Decision | Reason | Ladder rung (L0–L3) |
|---|----------|--------|---------------------|
| 1 | one Mastra agent | few tools, one scope | L1 |

## Revisit when
A refund must wait for an approval, or answers must come from documents.
