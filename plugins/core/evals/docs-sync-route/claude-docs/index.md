# orders-api — knowledge base

| Doc | Contents |
|-----|----------|
| [architecture.md](architecture.md) | Express app, one router per resource, in-memory store |
| [entry-points.md](entry-points.md) | HTTP routes and their handlers |
| [stack.md](stack.md) | Node 22, Express 5, Vitest; `npm test`, `npm run dev` |

Constraints: every route lives in `src/routes/`; handlers stay thin and call `src/services/`.
