# FastAPI rules

## Validation

- All request bodies: Pydantic `BaseModel` — never `dict` or raw `request.json()`
- All path/query params: type-annotated in function signature
- Response models: always declare `response_model=` on routes

## Async

- All route handlers: `async def` — never mix sync and async
- DB operations: use async driver (`asyncpg`, `motor`, `sqlalchemy async`)
- Background tasks: `BackgroundTasks` for fire-and-forget, Celery for reliability

## Error handling

- Use `HTTPException` with appropriate status codes — never return error messages in 200 responses
- Custom exception handlers in `main.py` only — not in individual routes
- Validate at boundary, trust internal code

## Dependency injection

- Use `Depends()` for: auth, DB sessions, settings
- Never import global state inside route functions
- Settings: use `pydantic_settings.BaseSettings` — never raw `os.environ` in routes

## Security

- CORS: whitelist specific origins — never `allow_origins=["*"]` in production
- Auth: JWT validation in a `Depends()` dependency — never inline in routes
- Input sanitization at model level via Pydantic validators

## Response size

Truncate list responses to max 10 records. Return a `total` count alongside paginated results.
