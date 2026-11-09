---
paths:
  - "**/*.module.ts"
  - "**/*.controller.ts"
  - "**/*.service.ts"
  - "**/*.guard.ts"
  - "**/*.gateway.ts"
  - "**/*.filter.ts"
  - "**/*.pipe.ts"
---

# NestJS rules

Adds only what is NestJS-specific. The handler order, error shape, contract and owner-scoping rules are in core's `api-contract.md`, `data-access.md` and `app-structure.md`. Framework claims below cite docs.nestjs.com (read 2026-11-09).

## Layout — modular monolith

- One feature module per aggregate: `src/modules/<aggregate>/{<aggregate>.module,controller,service,repository,schema}.ts`. The module lists its controllers and providers and exports only what another module imports; everything else stays private ([modules](https://docs.nestjs.com/modules): providers are injectable only inside their module or where an importing module exports them).
- No `@Global()` feature modules. Import what you need; `@Global()` is for the root infrastructure module only (config, db, logger), registered once ([modules](https://docs.nestjs.com/modules): register global modules once, in the root or core module; making everything global "is not a recommended design practice").
- Cross-aggregate composition lives in the calling module's service, never in a controller and never by importing another aggregate's repository: import its module and call its exported service.
- Providers are singletons by default and stay that way. No `Scope.REQUEST` unless a provider genuinely needs per-request state: request scope bubbles up and makes every controller that depends on it request-scoped, which costs latency on every request ([injection scopes](https://docs.nestjs.com/fundamentals/injection-scopes): "Unless a provider must be request-scoped, we strongly recommend using the default singleton scope"). Read the current user from the request object in the guard or a param decorator instead.

## Controller = guard → pipe → service → DTO

- Every controller is `@UseGuards(SessionGuard)` (or the guard is bound globally through `APP_GUARD`, so it can inject providers). Guards run after middleware and before pipes and interceptors, so unauthenticated input is never parsed ([guards](https://docs.nestjs.com/guards): "Guards are executed after all middleware, but before any interceptor or pipe"). A guard that returns `false` yields 403 `ForbiddenException`; for a missing session throw `UnauthorizedException` yourself so the client gets 401 ([guards](https://docs.nestjs.com/guards)).
- Body, params and query are validated with the zod schemas from `packages/shared` (or `schema.ts`) through one `ZodValidationPipe` implementing `PipeTransform`, bound per parameter (`@Body(new ZodValidationPipe(createChannelSchema))`) or per handler (`@UsePipes`). The pipe throws `BadRequestException` on `schema.parse` failure ([pipes](https://docs.nestjs.com/pipes): the docs' own schema-validation example). No `class-validator` DTO classes beside zod: one validation mechanism per app.
- The current user comes from a `@CurrentUser()` param decorator built with `createParamDecorator` that reads what the guard attached to the request ([custom decorators](https://docs.nestjs.com/custom-decorators), [passport recipe](https://docs.nestjs.com/recipes/passport): the guard assigns the validated user to `req.user`). Never from a header or body field.
- The handler calls one service method with `(user.id, parsedInput)` and maps the result to the response DTO. No SQL, no `db.` call and no business rule in a controller; those are the service's and the repository's.
- Use `@nestjs/platform-fastify`: `NestFactory.create<NestFastifyApplication>(AppModule, new FastifyAdapter())`, and `app.listen(port, '0.0.0.0')` in containers, since Fastify binds to localhost by default ([performance](https://docs.nestjs.com/techniques/performance)). Express-only middleware and recipes may not work there; check before adding one ([performance](https://docs.nestjs.com/techniques/performance): "recipes that rely on Express may not work").

## Errors — one filter

- One `@Catch()` filter with an empty parameter list, registered once through `APP_FILTER`, maps every thrown error to `{ error: <code> }` with the status from `api-contract.md` ([exception filters](https://docs.nestjs.com/exception-filters): an empty `@Catch()` catches every unhandled exception; `APP_FILTER` lets the filter inject dependencies). It writes the response through `HttpAdapterHost` so it stays adapter-agnostic ([exception filters](https://docs.nestjs.com/exception-filters)). Nest's default body (`statusCode` + `message`) never reaches a client.
- Services throw domain errors (`AppError('channel_not_found', 404)` or the app's equivalent). Controllers never `try/catch` to build an error response.
- Global filters do not cover gateways ([exception filters](https://docs.nestjs.com/exception-filters): "global filters do not apply to gateways or hybrid applications"), so the gateway binds a `WsException` filter with the same code mapping; the same `AppError` class feeds both.

## Permissions — one service for REST and Socket.IO

- One `PermissionService` (its own module, exported) answers "may `userId` do X on `resourceId`"; both HTTP guards and gateway guards call it. Never duplicate a channel membership check in a gateway handler.
- A websocket guard is the same class shape as an HTTP guard and throws `WsException` instead of `HttpException` ([ws guards](https://docs.nestjs.com/websockets/guards)). Bind it to the `@SubscribeMessage` handlers or the gateway class: guards are not applied to the connection itself, so authenticate the socket in a connection-level middleware or `handleConnection` and reject before any message is handled ([gateways](https://docs.nestjs.com/websockets/gateways)).
- Not found and not a member both answer 404 (`api-contract.md`); the same code comes back over the socket as an acknowledgement error.

## Gateways (Socket.IO)

- One gateway per module that pushes events (`<aggregate>.gateway.ts`), using `@nestjs/platform-socket.io`. Gateways are providers: list them in the module's `providers` or they are never instantiated ([gateways](https://docs.nestjs.com/websockets/gateways): "Gateways are not instantiated until they are referenced in the providers array of an existing module"), and inject the services they fan out from. A service that needs to emit injects the gateway, never the raw `Server`.
- Rooms are the permission boundary: on connect, join the socket to `user:<id>` and to `channel:<id>` for each channel the `PermissionService` lists; emit to rooms, never to all sockets. Leave the room when membership ends.
- Message payloads go through the same `ZodValidationPipe` as HTTP bodies ([gateways](https://docs.nestjs.com/websockets/gateways): pipes and filters "apply equally to gateways"). Returning a value from a `@SubscribeMessage` handler sends it as the acknowledgement ([gateways](https://docs.nestjs.com/websockets/gateways)); use that for request/response events instead of a second emit.

## Config

- `ConfigModule.forRoot({ isGlobal: true, validate })` where `validate` parses `process.env` with a zod schema and returns the typed result; a failed parse aborts bootstrap ([configuration](https://docs.nestjs.com/techniques/configuration): "If the function throws an error, the application doesn't bootstrap"). Nothing reads `process.env` after bootstrap: inject `ConfigService` (or a typed `Env` provider built from the parsed schema).
- Secrets come only from env; `.env` files stay out of git (`security.md`).

## Jobs (pg-boss)

- pg-boss is its own module (`src/modules/jobs/`): it owns the `PgBoss` instance, starts it in `onModuleInit`, stops it in `onModuleDestroy`, and exports a thin `JobsService` with `send(queue, payload)`. Queue names and payload zod schemas live beside it; a worker validates its payload with the same schema before working.
- Workers (`boss.work`) register in the module that owns the business logic and call that module's service, so a job and a request run the same code. No business logic in the jobs module.
- Job tables live in pg-boss's own schema; never reference them from app queries or Drizzle schema.

## Logging

- `nestjs-pino`: `LoggerModule.forRoot({ pinoHttp })` once, in the root module; the app is created with `bufferLogs: true` and `app.useLogger(app.get(Logger))` runs before `app.init()`/`listen()` ([nestjs-pino README](https://github.com/iamolegga/nestjs-pino), read 2026-11-09; [logger](https://docs.nestjs.com/techniques/logger): `bufferLogs` holds startup logs until a custom logger is attached). Nest's own `Logger` from `@nestjs/common` is what services inject; the pino binding happens once.
- `pinoHttp.redact` lists `req.headers.authorization`, `req.headers.cookie`, `req.body.password` and every token or secret field the app has. No `console.log` in app code. Never log a request body wholesale.

## Testing — real Postgres, Vitest

- Route and repository tests run against a real Postgres (a test database created per run, migrated with the same migrations as production), never a mocked `db`. Only the session is faked, by overriding the session guard or seeding a session row ([testing](https://docs.nestjs.com/fundamentals/testing): `Test.createTestingModule(...).overrideProvider(...)`; a globally registered guard must be bound with `useExisting` to be overridable).
- E2E on Fastify: `app = moduleRef.createNestApplication<NestFastifyApplication>(new FastifyAdapter())`, `await app.init()`, `await app.getHttpAdapter().getInstance().ready()`, then `app.inject({...})` without a listening port ([testing](https://docs.nestjs.com/fundamentals/testing)). Close the app and the pool in `afterAll`.
- Tests live in `__tests__/` beside the module (`testing.md`); the matrix per route is 200 · 400 · 401 · 404 for another user's resource, plus 403 where roles exist.
