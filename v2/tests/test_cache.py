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
