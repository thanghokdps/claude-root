import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { paymentsApi } from "./payments-api";

export const issueRefund = createTool({
  id: "issueRefund",
  description: "Refund one of the caller's paid orders in full.",
  inputSchema: z.object({ code: z.string().regex(/^DH\d{4,}$/) }),
  outputSchema: z.object({ refundId: z.string() }),
  execute: async (input, context) => {
    const tenantId = context.requestContext.get("tenantId") as string;
    return paymentsApi.refund(tenantId, input.code);
  },
});
