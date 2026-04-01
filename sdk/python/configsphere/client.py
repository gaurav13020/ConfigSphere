"""ConfigSphereClient — main entry point for the ConfigSphere SDK."""

from datetime import datetime
from typing import Any, Callable

from configsphere.backoff import BackoffStrategy
from configsphere.cache import ConfigCache
from configsphere.errors import ClientClosedError, ConfigNotAvailableError
from configsphere.logger import get_logger
from configsphere.models import ResolvedConfig, SDKConfig
from configsphere.poller import Poller
from configsphere.transport import HttpTransport


class ConfigSphereClient:
    """Client for real-time configuration management.

    Polls the ConfigSphere server in the background and maintains
    a thread-safe in-memory cache of the resolved configuration.

    Usage:
        config = SDKConfig(
            server_url="http://localhost:8000/api/v1",
            scope=ScopeParams(service_name="payment-svc"),
        )
        with ConfigSphereClient(config) as client:
            db_url = client.get("database_url")
    """

    def __init__(self, config: SDKConfig):
        self._config = config
        self._logger = get_logger(config.logger_name)
        self._transport = HttpTransport(config)
        self._cache = ConfigCache()
        self._backoff = BackoffStrategy(
            base_sec=config.base_backoff_sec,
            multiplier=config.backoff_multiplier,
            max_sec=config.max_backoff_sec,
            jitter=config.backoff_jitter,
        )
        self._callbacks: list[Callable[[dict], None]] = []
        self._poller: Poller | None = None
        self._closed = False

    def start(self) -> None:
        """Start background polling. Performs one synchronous fetch first (fail-fast)."""
        self._ensure_open()
        self._logger.info("Starting ConfigSphere client for %s", self._config.scope.service_name)

        self._poller = Poller(
            config=self._config,
            transport=self._transport,
            cache=self._cache,
            backoff=self._backoff,
            on_change_callbacks=self._callbacks,
        )
        self._poller.poll_once()

        if not self._cache.is_populated:
            raise ConfigNotAvailableError(
                "Failed to fetch initial configuration from server. "
                f"Server URL: {self._config.server_url}"
            )

        self._logger.info("Initial config loaded (checksum=%s)", self._cache.etag)
        self._poller.start()

    def close(self) -> None:
        """Stop polling and release resources. Idempotent."""
        if self._closed:
            return
        self._closed = True
        if self._poller is not None:
            self._poller.stop()
        self._transport.close()
        self._logger.info("ConfigSphere client closed")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a single config value from the in-memory cache."""
        self._ensure_open()
        return self._cache.get_value(key, default)

    def get_all(self) -> dict[str, Any]:
        """Get the full merged payload from cache."""
        self._ensure_open()
        config = self._cache.get()
        if config is None:
            return {}
        return dict(config.payload)

    def get_config(self) -> ResolvedConfig | None:
        """Get the full ResolvedConfig object (includes layers, checksum, metadata)."""
        self._ensure_open()
        return self._cache.get()

    def on_change(self, callback: Callable[[dict], None]) -> None:
        """Register a callback invoked when config changes. Receives diff dict."""
        self._callbacks.append(callback)

    def is_connected(self) -> bool:
        """Whether the last poll was successful."""
        if self._poller is None:
            return False
        return self._poller.last_poll_ok

    @property
    def etag(self) -> str | None:
        """Current ETag from server."""
        return self._cache.etag

    @property
    def last_updated(self) -> datetime | None:
        """When the cache was last updated."""
        return self._cache.last_updated_at

    def __enter__(self) -> "ConfigSphereClient":
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise ClientClosedError("Cannot perform operations on a closed client")
