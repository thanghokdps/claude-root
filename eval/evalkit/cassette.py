"""Record/replay cache for expensive calls (the LLM judge).

This is the "cache the conversation so re-runs don't burn tokens" idea: the first
run records each call keyed by a hash of its input; later runs replay the stored
result instead of calling the model again. Deterministic and free on replay.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Callable


class Cassette:
    def __init__(self, path: str, enabled: bool = True):
        self.path = path
        self.enabled = enabled
        self.data: dict[str, Any] = {}
        self.hits = 0
        self.misses = 0
        if enabled and os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                self.data = json.load(fh)

    @staticmethod
    def key(payload: Any) -> str:
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def call(self, payload: Any, produce: Callable[[], Any]) -> Any:
        """Return cached value for `payload`, or run `produce()` and cache it."""
        if not self.enabled:
            return produce()
        k = self.key(payload)
        if k in self.data:
            self.hits += 1
            return self.data[k]
        self.misses += 1
        value = produce()
        self.data[k] = value
        self._save()
        return value

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2, ensure_ascii=False)
