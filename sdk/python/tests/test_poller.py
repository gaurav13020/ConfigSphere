import time
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from configsphere.backoff import BackoffStrategy
from configsphere.cache import ConfigCache
from configsphere.errors import ServerError
from configsphere.models import ConfigLayer, ResolvedConfig, SDKConfig, ScopeParams
from configsphere.poller import Poller
from configsphere.transport import HttpTransport


def _make_config(payload: dict, checksum: str = "abc") -> ResolvedConfig:
    return ResolvedConfig(
        payload=payload,
        checksum=checksum,
        layers=(
            ConfigLayer(
                scope_level="global",
                config_item_id=1,
                config_version_id=1,
                version_number=1,
                checksum=checksum,
                key="test",
            ),
        ),
        scope_params=ScopeParams(service_name="test-svc"),
        fetched_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sdk_config():
    return SDKConfig(
        server_url="http://localhost:8000/api/v1",
        scope=ScopeParams(service_name="test-svc"),
        poll_interval_sec=0.1,
        base_backoff_sec=0.05,
        max_backoff_sec=0.5,
    )


@pytest.fixture
def mock_transport():
    return MagicMock(spec=HttpTransport)


@pytest.fixture
def cache():
    return ConfigCache()


@pytest.fixture
def backoff_strategy(sdk_config):
    return BackoffStrategy(
        base_sec=sdk_config.base_backoff_sec,
        multiplier=sdk_config.backoff_multiplier,
        max_sec=sdk_config.max_backoff_sec,
        jitter=False,
    )


class TestPollerLifecycle:
    def test_poll_once_success(self, sdk_config, mock_transport, cache, backoff_strategy):
        config = _make_config({"key": "value"}, checksum="ck1")
        mock_transport.fetch_resolved_config.return_value = (config, "ck1")

        poller = Poller(
            config=sdk_config,
            transport=mock_transport,
            cache=cache,
            backoff=backoff_strategy,
        )
        poller.poll_once()

        assert cache.get_value("key") == "value"
        assert cache.etag == "ck1"

    def test_poll_once_304_no_update(self, sdk_config, mock_transport, cache, backoff_strategy):
        initial = _make_config({"key": "old"})
        cache.update(initial, "etag_old")

        mock_transport.fetch_resolved_config.return_value = (None, "etag_old")

        poller = Poller(
            config=sdk_config,
            transport=mock_transport,
            cache=cache,
            backoff=backoff_strategy,
        )
        poller.poll_once()

        assert cache.get_value("key") == "old"

    def test_poll_once_error_uses_backoff(self, sdk_config, mock_transport, cache, backoff_strategy):
        mock_transport.fetch_resolved_config.side_effect = ServerError(500, "fail")

        poller = Poller(
            config=sdk_config,
            transport=mock_transport,
            cache=cache,
            backoff=backoff_strategy,
        )
        poller.poll_once()

        assert backoff_strategy.current_attempt == 1

    def test_on_change_callback_fires(self, sdk_config, mock_transport, cache, backoff_strategy):
        callback = MagicMock()
        config = _make_config({"key": "value"})
        mock_transport.fetch_resolved_config.return_value = (config, "ck1")

        poller = Poller(
            config=sdk_config,
            transport=mock_transport,
            cache=cache,
            backoff=backoff_strategy,
            on_change_callbacks=[callback],
        )
        poller.poll_once()

        callback.assert_called_once()
        diff = callback.call_args[0][0]
        assert "key" in diff

    def test_on_change_not_fired_when_no_diff(self, sdk_config, mock_transport, cache, backoff_strategy):
        callback = MagicMock()
        config = _make_config({"key": "value"})
        cache.update(config, "ck1")

        mock_transport.fetch_resolved_config.return_value = (config, "ck1")

        poller = Poller(
            config=sdk_config,
            transport=mock_transport,
            cache=cache,
            backoff=backoff_strategy,
            on_change_callbacks=[callback],
        )
        poller.poll_once()

        callback.assert_not_called()

    def test_start_and_stop(self, sdk_config, mock_transport, cache, backoff_strategy):
        config = _make_config({"key": "value"})
        mock_transport.fetch_resolved_config.return_value = (config, "ck1")

        poller = Poller(
            config=sdk_config,
            transport=mock_transport,
            cache=cache,
            backoff=backoff_strategy,
        )
        poller.start()
        time.sleep(0.3)
        poller.stop()

        assert not poller.is_running
        assert mock_transport.fetch_resolved_config.call_count >= 2

    def test_backoff_resets_on_success_after_failure(self, sdk_config, mock_transport, cache, backoff_strategy):
        config = _make_config({"key": "value"})

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ServerError(500, "fail")
            return (config, "ck1")

        mock_transport.fetch_resolved_config.side_effect = side_effect

        poller = Poller(
            config=sdk_config,
            transport=mock_transport,
            cache=cache,
            backoff=backoff_strategy,
        )
        poller.poll_once()
        assert backoff_strategy.current_attempt == 1

        poller.poll_once()
        assert backoff_strategy.current_attempt == 0
