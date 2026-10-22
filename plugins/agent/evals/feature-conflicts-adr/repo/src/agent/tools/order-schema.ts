import { z } from "zod";

export const OrderCode = z.string().regex(/^DH\d{4,}$/, "order code looks like DH1024");
export type Order = { code: string; status: "pending" | "shipping" | "delivered"; carrier: string; eta: string; total: number };
