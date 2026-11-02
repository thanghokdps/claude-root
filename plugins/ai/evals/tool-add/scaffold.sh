#!/usr/bin/env bash
# Seeds the order assistant with only listOrders; the ADR and the order card already expect a getOrder tool.
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/../feature-conflicts-adr/repo/." .
rm src/agent/tools/get-order.ts
cat > src/agent/orders-agent.ts <<'TS'
import { createAgent, toolRetryMiddleware } from "langchain";
import { listOrders } from "./tools/list-orders";

const readTools = [listOrders];

export const ordersAgent = createAgent({
  model: "anthropic:claude-sonnet-5-5",
  tools: readTools,
  middleware: [toolRetryMiddleware({ tools: readTools, maxRetries: 2 })],
  systemPrompt: "You answer questions about the customer's own orders. Read-only: for changes, cancellations or refunds, point to the support form.",
});
TS
