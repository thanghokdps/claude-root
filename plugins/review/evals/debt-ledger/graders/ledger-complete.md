---
type: llm
---

The repo has three `shortcut:` comments: `src/sync.py` (60 s polling, upgrade past 50 shops), `src/cache.ts` (in-memory map, upgrade to Redis past one instance) and `src/mailer.py` ("no retries", which names no upgrade trigger). README.md mentions a "keyboard shortcut: Ctrl+K", which is not a deferral.

PASS if the answer lists all three code shortcuts with their file (and line), gives the limit and upgrade trigger for sync.py and cache.ts, marks mailer.py as having no upgrade trigger, and does not list the README keyboard shortcut as debt.
FAIL if any of the three is missing, mailer.py is not singled out for its missing trigger, or the README line is listed.
