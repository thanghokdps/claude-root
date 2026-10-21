import { tool } from "@langchain/core/tools";
import { z } from "zod";
import type { Order } from "./order-schema";
import { ordersApi } from "./orders-client";

export const listOrders = tool(
  async (_input, config) => ordersApi<Order[]>("/orders?mine=1", config.configurable.token),
  { name: "listOrders", description: "- Use to list the customer's orders\n- Returns code and status per order", schema: z.object({}) },
);
