#!/usr/bin/env bash
# Seeds the order assistant with only listOrders; the ADR and the order card already expect a getOrder tool.
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/../feature-conflicts-adr/repo/." .
rm src/agent/tools/get-order.ts
# A test runner already in place, so the new tool's test needs no package.json change.
cat > package.json <<'JSON'
{ "name": "shopbot", "private": true, "type": "module",
  "scripts": { "test": "vitest run" },
  "dependencies": { "@copilotkit/react-core": "1.50.0", "@copilotkit/runtime": "1.50.0", "langchain": "1.0.4", "@langchain/core": "1.0.3", "zod": "3.25.76" },
  "devDependencies": { "vitest": "3.2.4" } }
JSON
# Tool names already shared (rules/agent-identity-and-tools.md), so the change stays inside the tool and the agent.
mkdir -p src/shared
cat > src/shared/tool-names.ts <<'TS'
export const LIST_ORDERS_TOOL = "listOrders";
export const GET_ORDER_TOOL = "getOrder";
TS
cat > src/agent/tools/list-orders.ts <<'TS'
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { LIST_ORDERS_TOOL } from "../../shared/tool-names";
import type { Order } from "./order-schema";
import { ordersApi } from "./orders-client";

export const listOrders = tool(
  async (_input, config) => ordersApi<Order[]>("/orders?mine=1", config.configurable.token),
  { name: LIST_ORDERS_TOOL, description: "- Use to list the customer's orders\n- Returns code and status per order", schema: z.object({}) },
);
TS
cat > src/web/OrderCard.tsx <<'TSX'
import { useRenderTool } from "@copilotkit/react-core/v2";
import { GET_ORDER_TOOL } from "../shared/tool-names";

export function useOrderCard() {
  useRenderTool({
    name: GET_ORDER_TOOL,
    render: ({ result }) =>
      !result ? <div>…</div>
      : result.found === false ? <div className="order-card">{result.message}</div>
      : <div className="order-card">{result.code} — {result.status}</div>,
  });
}
TSX
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
