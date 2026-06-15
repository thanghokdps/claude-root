# Python rules

## Quality gate

```bash
ruff check .          # lint + format check
ruff format --check . # format only
mypy src/             # type check (if mypy configured)
pytest -q             # tests
```

## Style

- Line length: 88 (ruff default, matches black)
- Use `ruff` for both linting and formatting — never mix with black/flake8
- Type hints required on all public function signatures
- `Optional[X]` → prefer `X | None` (Python 3.10+)

## Patterns

- Pydantic for data validation at system boundaries (API input, external responses)
- `dataclass` for internal data structures with no validation
- Never use bare `except:` — always `except SpecificException as e:`
- Logging: `logging.getLogger(__name__)` — never `print()` in production code

## Async

- Use `async/await` throughout if any I/O is async — never mix sync and async in the same request path
- `asyncio.run()` only at top-level entry points

## Debug artifacts

- Never commit `breakpoint()` or `pdb.set_trace()` — enforced by commit gate
- `print()` in app code is blocked by commit gate — use `logging` instead

## No raw text parsing from LLMs

```python
# WRONG
response = model.invoke(messages)
result = json.loads(response.content)  # fragile

# CORRECT
result = model.with_structured_output(MySchema).invoke(messages)
```
