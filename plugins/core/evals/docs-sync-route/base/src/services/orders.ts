export type Order = { id: string; total: number; status: "paid" | "refunded" };

const store = new Map<string, Order>([["A1", { id: "A1", total: 120, status: "paid" }]]);

export const all = () => [...store.values()];
export const byId = (id: string) => store.get(id);
