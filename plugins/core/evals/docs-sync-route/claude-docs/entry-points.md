# Entry points

App start: `src/server.ts` mounts `src/routes/orders.ts` on `/`.

## HTTP routes

| Method | Path | Handler |
|--------|------|---------|
| GET | /orders | `src/routes/orders.ts` → `listOrders` |
| GET | /orders/:id | `src/routes/orders.ts` → `getOrder` |
