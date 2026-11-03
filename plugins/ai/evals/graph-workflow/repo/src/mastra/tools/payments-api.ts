const base = process.env.PAYMENTS_API_URL ?? "http://localhost:4100";

export const paymentsApi = {
  async refund(tenantId: string, code: string) {
    const res = await fetch(`${base}/tenants/${tenantId}/refunds`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ orderCode: code }),
    });
    if (!res.ok) throw new Error(`payments API ${res.status}`);
    return res.json();
  },
};
