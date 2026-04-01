import responses
import pytest

from configsphere.transport import HttpTransport
from configsphere.models import SDKConfig, ScopeParams
from configsphere.errors import ServerError, ServerUnreachableError, InvalidResponseError
from tests.conftest import SAMPLE_CHECKSUM, SAMPLE_RESPONSE_BODY


@pytest.fixture
def sdk_config(sample_scope):
    return SDKConfig(
        server_url="http://localhost:8000/api/v1",
        scope=sample_scope,
        request_timeout_sec=5.0,
    )


@pytest.fixture
def transport(sdk_config):
    return HttpTransport(sdk_config)


class TestUrlConstruction:
    @responses.activate
    def test_builds_url_with_all_scope_params(self, transport):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        transport.fetch_resolved_config(
            ScopeParams(
                service_name="payment-svc",
                region_name="us-west",
                group_name="checkout",
                global_name="prod",
            ),
            etag=None,
        )
        assert "service=payment-svc" in responses.calls[0].request.url
        assert "region=us-west" in responses.calls[0].request.url
        assert "group=checkout" in responses.calls[0].request.url
        assert "global=prod" in responses.calls[0].request.url

    @responses.activate
    def test_omits_none_scope_params(self, transport):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        transport.fetch_resolved_config(
            ScopeParams(service_name="payment-svc"),
            etag=None,
        )
        url = responses.calls[0].request.url
        assert "service=payment-svc" in url
        assert "region" not in url
        assert "group" not in url
        assert "global=default" in url


class TestSuccessResponse:
    @responses.activate
    def test_returns_resolved_config_on_200(self, transport, sample_scope):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        config, etag = transport.fetch_resolved_config(sample_scope, etag=None)
        assert config is not None
        assert config.payload["database_url"] == "postgres://localhost:5432/mydb"
        assert config.checksum == SAMPLE_CHECKSUM
        assert len(config.layers) == 2
        assert config.layers[0].scope_level == "global"
        assert config.scope_params.service_name == "payment-svc"
        assert etag == SAMPLE_CHECKSUM

    @responses.activate
    def test_sends_if_none_match_header(self, transport, sample_scope):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        transport.fetch_resolved_config(sample_scope, etag="prev_etag")
        assert responses.calls[0].request.headers["If-None-Match"] == '"prev_etag"'

    @responses.activate
    def test_no_if_none_match_when_etag_is_none(self, transport, sample_scope):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        transport.fetch_resolved_config(sample_scope, etag=None)
        assert "If-None-Match" not in responses.calls[0].request.headers


class TestNotModifiedResponse:
    @responses.activate
    def test_returns_none_config_on_304(self, transport, sample_scope):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            status=304,
        )
        config, etag = transport.fetch_resolved_config(sample_scope, etag="existing")
        assert config is None
        assert etag == "existing"


class TestErrorResponses:
    @responses.activate
    def test_raises_server_error_on_500(self, transport, sample_scope):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            status=500,
            body="Internal Server Error",
        )
        with pytest.raises(ServerError) as exc_info:
            transport.fetch_resolved_config(sample_scope, etag=None)
        assert exc_info.value.status_code == 500

    @responses.activate
    def test_raises_invalid_response_on_400(self, transport, sample_scope):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            status=400,
            body="Bad Request",
        )
        with pytest.raises(InvalidResponseError):
            transport.fetch_resolved_config(sample_scope, etag=None)

    @responses.activate
    def test_raises_server_unreachable_on_connection_error(self, transport, sample_scope):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            body=ConnectionError("Connection refused"),
        )
        with pytest.raises(ServerUnreachableError):
            transport.fetch_resolved_config(sample_scope, etag=None)

    @responses.activate
    def test_raises_invalid_response_on_malformed_json(self, transport, sample_scope):
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            body="not json",
            status=200,
            headers={"ETag": '"abc"'},
        )
        with pytest.raises(InvalidResponseError):
            transport.fetch_resolved_config(sample_scope, etag=None)


class TestAuthToken:
    @responses.activate
    def test_sends_authorization_header(self, sample_scope):
        cfg = SDKConfig(
            server_url="http://localhost:8000/api/v1",
            scope=sample_scope,
            auth_token="Bearer tok123",
        )
        transport = HttpTransport(cfg)
        responses.add(
            responses.GET,
            "http://localhost:8000/api/v1/resolved-config/",
            json=SAMPLE_RESPONSE_BODY,
            headers={"ETag": f'"{SAMPLE_CHECKSUM}"'},
        )
        transport.fetch_resolved_config(sample_scope, etag=None)
        assert responses.calls[0].request.headers["Authorization"] == "Bearer tok123"
