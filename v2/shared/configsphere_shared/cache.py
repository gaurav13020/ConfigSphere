from __future__ import annotations

import json
import logging
import time
from decimal import Decimal
from typing import Any

import redis as redis_lib
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class _CacheEncoder(json.JSONEncoder):
    """JSON encoder that converts Decimal to float/int for Redis serialisation."""

    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            # Preserve int precision when the value has no fractional part.
            return int(o) if o == o.to_integral_value() else float(o)
        return super().default(o)


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


class TwoTierCache:
    """Two-tier cache: L1 in-memory + L2 Redis (sync). Redis errors are non-fatal."""

    def __init__(
        self,
        redis_client: redis_lib.Redis,
        l1_ttl_seconds: int = 600,
        l2_ttl_seconds: int = 1800,
        l1_max_size: int = 5000,
    ) -> None:
        self.l1 = L1Cache(ttl_seconds=l1_ttl_seconds, max_size=l1_max_size)
        self._redis = redis_client
        self._l2_ttl = l2_ttl_seconds

    def get(self, key: str) -> Any | None:
        value = self.l1.get(key)
        if value is not None:
            return value
        try:
            raw = self._redis.get(key)
            if raw is not None:
                value = json.loads(raw)
                self.l1.set(key, value)
                return value
        except RedisError:
            logger.warning("Redis unavailable on GET: %s", key)
        return None

    def set(self, key: str, value: Any) -> None:
        self.l1.set(key, value)
        try:
            self._redis.setex(key, self._l2_ttl, json.dumps(value, cls=_CacheEncoder))
        except RedisError:
            logger.warning("Redis unavailable on SET: %s", key)

    def delete(self, key: str) -> None:
        self.l1.delete(key)
        try:
            self._redis.delete(key)
        except RedisError:
            logger.warning("Redis unavailable on DELETE: %s", key)
