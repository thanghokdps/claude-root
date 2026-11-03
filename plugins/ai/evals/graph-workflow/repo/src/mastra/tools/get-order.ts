import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { ordersApi } from "./orders-api";

export const getOrder = createTool({
  id: "getOrder",
  description: "Read one of the caller's orders by its code.",
  inputSchema: z.object({ code: z.string().regex(/^DH\d{4,}$/) }),
  outputSchema: z.object({ code: z.string(), status: z.string(), total: z.number(), paidAt: z.string().nullable() }),
  execute: async (input, context) => {
    const tenantId = context.requestContext.get("tenantId") as string;
    return ordersApi.get(tenantId, input.code);
  },
});
