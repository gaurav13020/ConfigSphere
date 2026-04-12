from __future__ import annotations

import time
from typing import Any


class L1Cache:
    """In-process TTL cache. Not thread-safe; safe for asyncio single-threaded use."""

    def __init__(self, ttl_seconds: int = 600, max_size: int = 5000) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        if len(self._store) >= self._max_size:
            self._evict()
        self._store[key] = (value, time.monotonic() + self._ttl)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def _evict(self) -> None:
        count = max(1, len(self._store) // 10)
        oldest = sorted(self._store.items(), key=lambda item: item[1][1])[:count]
        for key, _ in oldest:
            del self._store[key]
