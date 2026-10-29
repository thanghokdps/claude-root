# Architecture

| Path | Responsibility |
|------|----------------|
| `src/server.ts` | Express app, mounts routers |
| `src/routes/` | One router per resource; validates input, calls a service |
| `src/services/orders.ts` | Order rules over the in-memory store |
