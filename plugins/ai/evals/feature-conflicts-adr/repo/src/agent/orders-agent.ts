import { createAgent, toolRetryMiddleware } from "langchain";
import { getOrder } from "./tools/get-order";
import { listOrders } from "./tools/list-orders";

const readTools = [getOrder, listOrders];

export const ordersAgent = createAgent({
  model: "anthropic:claude-sonnet-5-5",
  tools: readTools,
  middleware: [toolRetryMiddleware({ tools: readTools, maxRetries: 2 })],
  systemPrompt: "You answer questions about the customer's own orders. Read-only: for changes, cancellations or refunds, point to the support form.",
});
