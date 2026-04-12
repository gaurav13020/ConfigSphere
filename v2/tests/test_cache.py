from __future__ import annotations

import time

import pytest

from configsphere_shared.cache import L1Cache


def test_get_returns_none_for_missing_key():
    cache = L1Cache()
    assert cache.get("missing") is None


def test_set_and_get_returns_value():
    cache = L1Cache()
    cache.set("k", {"foo": "bar"})
    assert cache.get("k") == {"foo": "bar"}


def test_get_returns_none_after_ttl_expires():
    cache = L1Cache(ttl_seconds=0)
    cache.set("k", {"foo": "bar"})
    time.sleep(0.01)
    assert cache.get("k") is None


def test_expired_entry_is_removed_from_store():
    cache = L1Cache(ttl_seconds=0)
    cache.set("k", {"foo": "bar"})
    time.sleep(0.01)
    cache.get("k")
    assert "k" not in cache._store


def test_delete_removes_entry():
    cache = L1Cache()
    cache.set("k", {"foo": "bar"})
    cache.delete("k")
    assert cache.get("k") is None


def test_delete_on_missing_key_does_not_raise():
    cache = L1Cache()
    cache.delete("nonexistent")  # must not raise


def test_evicts_when_max_size_reached():
    cache = L1Cache(max_size=10)
    for i in range(11):
        cache.set(f"key{i}", {"val": i})
    assert len(cache._store) <= 10


def test_entries_added_after_eviction_are_stored():
    cache = L1Cache(max_size=5)
    for i in range(6):
        cache.set(f"key{i}", {"val": i})
    cache.set("new", {"val": 99})
    assert cache.get("new") == {"val": 99}


from unittest.mock import MagicMock

import redis as redis_lib
from redis.exceptions import RedisError

from configsphere_shared.cache import TwoTierCache


def _make_mock_redis(get_return=None, raise_on=None):
    """Build a mock redis.Redis where methods optionally raise RedisError."""
    r = MagicMock(spec=redis_lib.Redis)
    if raise_on == "get":
        r.get.side_effect = RedisError("down")
    else:
        r.get.return_value = get_return
    if raise_on == "setex":
        r.setex.side_effect = RedisError("down")
    if raise_on == "delete":
        r.delete.side_effect = RedisError("down")
    return r


def test_two_tier_get_returns_none_when_both_miss():
    cache = TwoTierCache(_make_mock_redis())
    assert cache.get("k") is None


def test_two_tier_get_from_l2_populates_l1():
    r = _make_mock_redis(get_return='{"foo": "bar"}')
    cache = TwoTierCache(r)
    result = cache.get("k")
    assert result == {"foo": "bar"}
    assert cache.l1.get("k") == {"foo": "bar"}


def test_two_tier_get_from_l1_skips_redis():
    r = _make_mock_redis()
    cache = TwoTierCache(r)
    cache.l1.set("k", {"cached": True})
    assert cache.get("k") == {"cached": True}
    r.get.assert_not_called()


def test_two_tier_set_writes_both_layers():
    r = _make_mock_redis()
    cache = TwoTierCache(r, l2_ttl_seconds=1800)
    cache.set("k", {"v": 1})
    assert cache.l1.get("k") == {"v": 1}
    r.setex.assert_called_once_with("k", 1800, '{"v": 1}')


def test_two_tier_delete_evicts_both_layers():
    r = _make_mock_redis()
    cache = TwoTierCache(r)
    cache.l1.set("k", {"v": 1})
    cache.delete("k")
    assert cache.l1.get("k") is None
    r.delete.assert_called_once_with("k")


def test_two_tier_get_returns_none_when_redis_down():
    cache = TwoTierCache(_make_mock_redis(raise_on="get"))
    assert cache.get("k") is None  # must not raise


def test_two_tier_set_still_populates_l1_when_redis_down():
    cache = TwoTierCache(_make_mock_redis(raise_on="setex"))
    cache.set("k", {"v": 1})  # must not raise
    assert cache.l1.get("k") == {"v": 1}


def test_two_tier_delete_clears_l1_when_redis_down():
    cache = TwoTierCache(_make_mock_redis(raise_on="delete"))
    cache.l1.set("k", {"v": 1})
    cache.delete("k")  # must not raise
    assert cache.l1.get("k") is None
