import type { Order } from "./order-schema";

export async function ordersApi<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`${process.env.ORDERS_API_URL}${path}`, { headers: { authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error(`orders api ${res.status}`);
  return (await res.json()) as T;
}
export type { Order };
