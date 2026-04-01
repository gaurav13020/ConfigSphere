"""Background polling thread for fetching config updates."""

import threading
from typing import Callable

from configsphere.backoff import BackoffStrategy
from configsphere.cache import ConfigCache
from configsphere.errors import ConfigSphereError
from configsphere.logger import get_logger
from configsphere.models import SDKConfig
from configsphere.transport import HttpTransport

logger = get_logger()


class Poller:
    """Runs a background daemon thread that periodically polls the Config Server."""

    def __init__(
        self,
        config: SDKConfig,
        transport: HttpTransport,
        cache: ConfigCache,
        backoff: BackoffStrategy,
        on_change_callbacks: list[Callable[[dict], None]] | None = None,
    ):
        self._config = config
        self._transport = transport
        self._cache = cache
        self._backoff = backoff
        self._callbacks = on_change_callbacks or []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_poll_ok = False

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def last_poll_ok(self) -> bool:
        return self._last_poll_ok

    def poll_once(self) -> None:
        """Execute a single poll cycle. Used for initial sync and by the background loop."""
        try:
            config, etag = self._transport.fetch_resolved_config(
                self._config.scope, self._cache.etag
            )

            if config is not None and etag is not None:
                diff = self._cache.update(config, etag)
                if diff:
                    logger.info("Config changed: %d keys affected", len(diff))
                    self._fire_callbacks(diff)

            self._backoff.reset()
            self._last_poll_ok = True

        except ConfigSphereError as exc:
            self._last_poll_ok = False
            delay = self._backoff.next_delay()
            logger.warning(
                "Poll failed (attempt %d): %s — next retry in %.1fs",
                self._backoff.current_attempt,
                exc,
                delay,
            )

    def start(self) -> None:
        """Start the background polling thread."""
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop, name="configsphere-poller", daemon=True
        )
        self._thread.start()
        logger.info("Poller started (interval=%.1fs)", self._config.poll_interval_sec)

    def stop(self, timeout: float = 5.0) -> None:
        """Stop the polling thread and wait for it to finish."""
        self._stop_event.set()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning("Poller thread did not stop within %.1fs", timeout)
        self._thread = None
        logger.info("Poller stopped")

    def _run_loop(self) -> None:
        """Main polling loop — runs in the background thread."""
        while not self._stop_event.is_set():
            self.poll_once()

            if self._last_poll_ok:
                sleep_time = self._config.poll_interval_sec
            else:
                sleep_time = self._backoff._prev_delay

            self._stop_event.wait(timeout=sleep_time)

    def _fire_callbacks(self, diff: dict) -> None:
        """Invoke all registered on_change callbacks."""
        for callback in self._callbacks:
            try:
                callback(diff)
            except Exception:
                logger.exception("on_change callback raised an exception")
