"""Shared fixtures for ConfigSphere SDK tests."""

import pytest

from configsphere.models import ScopeParams


SAMPLE_PAYLOAD = {
    "database_url": "postgres://localhost:5432/mydb",
    "cache_ttl": 300,
    "feature_flags": {"dark_mode": True},
}

SAMPLE_CHECKSUM = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"

SAMPLE_RESPONSE_BODY = {
    "payload": SAMPLE_PAYLOAD,
    "checksum": SAMPLE_CHECKSUM,
    "layers": [
        {
            "scope_level": "global",
            "config_item_id": 1,
            "config_version_id": 3,
            "version_number": 2,
            "checksum": "abc123",
            "key": "database_config",
        },
        {
            "scope_level": "service",
            "config_item_id": 5,
            "config_version_id": 10,
            "version_number": 1,
            "checksum": "def456",
            "key": "feature_flags",
        },
    ],
    "scope_params": {
        "global_name": "default",
        "region_name": "us-west",
        "group_name": None,
        "service_name": "payment-svc",
    },
}


@pytest.fixture
def sample_scope() -> ScopeParams:
    return ScopeParams(service_name="payment-svc", region_name="us-west")


@pytest.fixture
def sample_response_body() -> dict:
    return SAMPLE_RESPONSE_BODY.copy()
