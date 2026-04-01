"""Thread-safe in-memory configuration cache."""

import threading
from datetime import datetime, timezone
from typing import Any

from configsphere.models import ResolvedConfig


class ConfigCache:
    """Stores the current resolved configuration with thread-safe access.

    All reads and writes are protected by a threading.Lock.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._config: ResolvedConfig | None = None
        self._etag: str | None = None
        self._last_updated_at: datetime | None = None

    def get(self) -> ResolvedConfig | None:
        """Return the current cached config, or None if empty."""
        with self._lock:
            return self._config

    def get_value(self, key: str, default: Any = None) -> Any:
        """Return a single key from the cached payload."""
        with self._lock:
            if self._config is None:
                return default
            return self._config.payload.get(key, default)

    def update(self, config: ResolvedConfig, etag: str) -> dict[str, dict[str, Any]]:
        """Atomically replace the cached config and return a diff of changed keys.

        Returns:
            Dict of {key: {"old": old_value, "new": new_value}} for all changed keys.
            Keys removed from the new config appear with new=None.
            Keys added appear with old=None.
        """
        with self._lock:
            old_payload = self._config.payload if self._config else {}
            new_payload = config.payload

            diff = self._compute_diff(old_payload, new_payload)

            self._config = config
            self._etag = etag
            self._last_updated_at = datetime.now(timezone.utc)

            return diff

    @property
    def etag(self) -> str | None:
        with self._lock:
            return self._etag

    @property
    def is_populated(self) -> bool:
        with self._lock:
            return self._config is not None

    @property
    def last_updated_at(self) -> datetime | None:
        with self._lock:
            return self._last_updated_at

    @staticmethod
    def _compute_diff(
        old: dict[str, Any], new: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        diff: dict[str, dict[str, Any]] = {}
        all_keys = set(old) | set(new)
        for key in all_keys:
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                diff[key] = {"old": old_val, "new": new_val}
        return diff
