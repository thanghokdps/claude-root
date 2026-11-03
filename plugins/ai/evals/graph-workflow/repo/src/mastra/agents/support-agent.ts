import { Agent } from "@mastra/core/agent";
import { getOrder } from "../tools/get-order";
import { issueRefund } from "../tools/issue-refund";

export const supportAgent = new Agent({
  id: "support",
  name: "support",
  instructions: "You help the shop's customers with their own orders and refunds.",
  model: "anthropic/claude-sonnet-5-5",
  tools: { getOrder, issueRefund },
});
