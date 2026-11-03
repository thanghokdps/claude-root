const base = process.env.ORDERS_API_URL ?? "http://localhost:4000";

export const ordersApi = {
  async get(tenantId: string, code: string) {
    const res = await fetch(`${base}/tenants/${tenantId}/orders/${code}`);
    if (!res.ok) throw new Error(`orders API ${res.status}`);
    return res.json();
  },
};
