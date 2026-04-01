import time
from datetime import datetime
from unittest.mock import MagicMock

import pytest
import responses

from configsphere.client import ConfigSphereClient
from configsphere.errors import ClientClosedError, ConfigNotAvailableError
from configsphere.models import SDKConfig, ScopeParams
from tests.conftest import SAMPLE_CHECKSUM, SAMPLE_RESPONSE_BODY


@pytest.fixture
def sdk_config():
    return SDKConfig(
        server_url="http://localhost:8000/api/v1",
        scope=ScopeParams(service_name="payment-svc", region_name="us-west"),
        poll_interval_sec=0.1,
    )


class TestClientLifecycle:
    @responses.activate
    def test_start_performs_initial_fetch(self, sdk_config):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        client = ConfigSphereClient(sdk_config)
        client.start()
        try:
            assert client.get("database_url") == "postgres://localhost:5432/mydb"
            assert client.etag == SAMPLE_CHECKSUM
        finally:
            client.close()

    @responses.activate
    def test_start_raises_on_cold_start_failure(self, sdk_config):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            body=ConnectionError("refused"),
        )
        client = ConfigSphereClient(sdk_config)
        with pytest.raises(ConfigNotAvailableError):
            client.start()

    @responses.activate
    def test_close_is_idempotent(self, sdk_config):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        client = ConfigSphereClient(sdk_config)
        client.start()
        client.close()
        client.close()  # Should not raise


class TestClientGet:
    @responses.activate
    def test_get_returns_value(self, sdk_config):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        with ConfigSphereClient(sdk_config) as client:
            assert client.get("database_url") == "postgres://localhost:5432/mydb"
            assert client.get("cache_ttl") == 300
            assert client.get("missing") is None
            assert client.get("missing", "fallback") == "fallback"

    @responses.activate
    def test_get_all_returns_full_payload(self, sdk_config):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        with ConfigSphereClient(sdk_config) as client:
            all_config = client.get_all()
            assert all_config == SAMPLE_RESPONSE_BODY["payload"]

    @responses.activate
    def test_get_config_returns_resolved_config(self, sdk_config):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        with ConfigSphereClient(sdk_config) as client:
            config = client.get_config()
            assert config is not None
            assert config.checksum == SAMPLE_CHECKSUM
            assert len(config.layers) == 2


class TestClientOnChange:
    @responses.activate
    def test_on_change_fires_on_update(self, sdk_config):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        updated_body = {
            **SAMPLE_RESPONSE_BODY,
            "payload": {**SAMPLE_RESPONSE_BODY["payload"], "cache_ttl": 600},
            "checksum": "newchecksum",
        }
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=updated_body,
            headers={"ETag": '"newchecksum"'},
        )

        callback = MagicMock()
        client = ConfigSphereClient(sdk_config)
        client.on_change(callback)
        client.start()
        time.sleep(0.3)
        client.close()

        assert callback.call_count >= 1


class TestClientContextManager:
    @responses.activate
    def test_context_manager(self, sdk_config):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        with ConfigSphereClient(sdk_config) as client:
            assert client.get("database_url") == "postgres://localhost:5432/mydb"


class TestClientProperties:
    @responses.activate
    def test_is_connected(self, sdk_config):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        with ConfigSphereClient(sdk_config) as client:
            assert client.is_connected() is True

    @responses.activate
    def test_last_updated(self, sdk_config):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        with ConfigSphereClient(sdk_config) as client:
            assert client.last_updated is not None
            assert isinstance(client.last_updated, datetime)

    def test_get_raises_after_close(self, sdk_config):
        client = ConfigSphereClient(sdk_config)
        client._closed = True
        with pytest.raises(ClientClosedError):
            client.get("key")
