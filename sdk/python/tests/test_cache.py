import threading
from datetime import datetime, timezone

import pytest

from configsphere.cache import ConfigCache
from configsphere.models import ConfigLayer, ResolvedConfig, ScopeParams


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


class TestConfigCache:
    def test_empty_cache_returns_none(self):
        cache = ConfigCache()
        assert cache.get() is None
        assert cache.get_value("key") is None
        assert cache.etag is None
        assert cache.is_populated is False

    def test_update_populates_cache(self):
        cache = ConfigCache()
        config = _make_config({"db_url": "localhost"})
        diff = cache.update(config, "etag1")
        assert cache.is_populated is True
        assert cache.get() is config
        assert cache.etag == "etag1"
        assert diff == {"db_url": {"old": None, "new": "localhost"}}

    def test_get_value_returns_payload_key(self):
        cache = ConfigCache()
        config = _make_config({"db_url": "localhost", "port": 5432})
        cache.update(config, "etag1")
        assert cache.get_value("db_url") == "localhost"
        assert cache.get_value("port") == 5432
        assert cache.get_value("missing") is None
        assert cache.get_value("missing", "default") == "default"

    def test_update_returns_diff_for_changed_keys(self):
        cache = ConfigCache()
        config1 = _make_config({"a": 1, "b": 2, "c": 3})
        cache.update(config1, "etag1")

        config2 = _make_config({"a": 1, "b": 99, "d": 4})
        diff = cache.update(config2, "etag2")

        assert diff == {
            "b": {"old": 2, "new": 99},
            "c": {"old": 3, "new": None},
            "d": {"old": None, "new": 4},
        }

    def test_update_returns_empty_diff_when_unchanged(self):
        cache = ConfigCache()
        config = _make_config({"a": 1})
        cache.update(config, "etag1")
        diff = cache.update(config, "etag1")
        assert diff == {}

    def test_last_updated_at(self):
        cache = ConfigCache()
        assert cache.last_updated_at is None
        config = _make_config({"a": 1})
        cache.update(config, "etag1")
        assert cache.last_updated_at is not None
        assert isinstance(cache.last_updated_at, datetime)


class TestConfigCacheThreadSafety:
    def test_concurrent_reads_and_writes(self):
        cache = ConfigCache()
        errors = []

        def writer():
            for i in range(100):
                config = _make_config({"counter": i}, checksum=f"ck{i}")
                cache.update(config, f"etag{i}")

        def reader():
            for _ in range(100):
                val = cache.get_value("counter")
                cfg = cache.get()
                etag = cache.etag
                if cfg is not None:
                    try:
                        assert isinstance(cfg.payload, dict)
                    except AssertionError as e:
                        errors.append(e)

        threads = [threading.Thread(target=writer) for _ in range(3)]
        threads += [threading.Thread(target=reader) for _ in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert errors == [], f"Thread safety errors: {errors}"
