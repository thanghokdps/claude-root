export type Order = { id: string; total: number; status: "paid" | "refunded" };

const store = new Map<string, Order>([["A1", { id: "A1", total: 120, status: "paid" }]]);

export const all = () => [...store.values()];
export const byId = (id: string) => store.get(id);

export function refund(id: string): Order | undefined {
  const order = store.get(id);
  if (!order || order.status === "refunded") return undefined;
  order.status = "refunded";
  return order;
}
