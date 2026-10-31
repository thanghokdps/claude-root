# URL shortener — design

Status: **approved** (2026-10-28)

## Goal

Turn a long URL into a short code and redirect the code back to the URL. One process, standard library only.

## Modules

| File | Job |
|------|-----|
| `src/codes.py` | `encode(n: int) -> str` and `decode(code: str) -> int` in base62 (`0-9a-zA-Z`); `decode` raises `ValueError` on a character outside the alphabet |
| `src/store.py` | `Store` keeps `code → url` in a dict; `add(url) -> code` gives each new URL the next integer id, encoded; the same URL twice returns its existing code; `get(code) -> str \| None` |
| `src/handler.py` | `handle(method, path, body, store) -> (status, headers, body)`: `POST /` with a URL body → `201` and the code; `GET /<code>` → `302` with `Location`; an unknown code → `404`; a body that is not an `http(s)://` URL → `400` |

## Tests

`unittest`, one file per module: `tests/test_codes.py`, `tests/test_store.py`, `tests/test_handler.py`. Run with `python3 -m unittest`.

## Out of scope

Persistence, expiry, custom codes, analytics.
