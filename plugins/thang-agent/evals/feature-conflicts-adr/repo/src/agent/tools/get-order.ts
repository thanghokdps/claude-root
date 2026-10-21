import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { OrderCode, type Order } from "./order-schema";
import { ordersApi } from "./orders-client";

export const getOrder = tool(
  async ({ code }, config) => ordersApi<Order>(`/orders/${code}`, config.configurable.token),
  { name: "getOrder", description: "- Use for one order by code\n- Returns status, carrier, ETA, total", schema: z.object({ code: OrderCode }) },
);
