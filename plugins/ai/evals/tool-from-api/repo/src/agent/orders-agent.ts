import { createAgent } from "langchain";

export const ordersAgent = createAgent({
  model: "anthropic:claude-sonnet-5-5",
  tools: [],
  systemPrompt: "You answer questions about the customer's own orders. No tools yet: say you cannot look orders up.",
});

export const graph = ordersAgent;
