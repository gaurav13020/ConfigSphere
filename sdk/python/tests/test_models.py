from datetime import datetime, timezone

import pytest

from configsphere.models import ConfigLayer, ResolvedConfig, SDKConfig, ScopeParams


class TestScopeParams:
    def test_defaults(self):
        scope = ScopeParams(service_name="payment-svc")
        assert scope.service_name == "payment-svc"
        assert scope.region_name is None
        assert scope.group_name is None
        assert scope.global_name == "default"

    def test_full_scope(self):
        scope = ScopeParams(
            service_name="payment-svc",
            region_name="us-west",
            group_name="checkout",
            global_name="prod",
        )
        assert scope.region_name == "us-west"
        assert scope.group_name == "checkout"
        assert scope.global_name == "prod"

    def test_immutable(self):
        scope = ScopeParams(service_name="payment-svc")
        with pytest.raises(AttributeError):
            scope.service_name = "other"


class TestConfigLayer:
    def test_construction(self):
        layer = ConfigLayer(
            scope_level="global",
            config_item_id=1,
            config_version_id=3,
            version_number=2,
            checksum="abc123",
            key="database_config",
        )
        assert layer.scope_level == "global"
        assert layer.config_item_id == 1
        assert layer.key == "database_config"

    def test_immutable(self):
        layer = ConfigLayer(
            scope_level="global",
            config_item_id=1,
            config_version_id=3,
            version_number=2,
            checksum="abc123",
            key="db",
        )
        with pytest.raises(AttributeError):
            layer.checksum = "new"


class TestResolvedConfig:
    def test_construction(self):
        now = datetime.now(timezone.utc)
        config = ResolvedConfig(
            payload={"db_url": "localhost"},
            checksum="sha256hex",
            layers=(
                ConfigLayer(
                    scope_level="global",
                    config_item_id=1,
                    config_version_id=3,
                    version_number=2,
                    checksum="abc",
                    key="db",
                ),
            ),
            scope_params=ScopeParams(service_name="svc"),
            fetched_at=now,
        )
        assert config.payload == {"db_url": "localhost"}
        assert config.checksum == "sha256hex"
        assert len(config.layers) == 1
        assert config.fetched_at == now

    def test_immutable(self):
        now = datetime.now(timezone.utc)
        config = ResolvedConfig(
            payload={},
            checksum="abc",
            layers=(),
            scope_params=ScopeParams(service_name="svc"),
            fetched_at=now,
        )
        with pytest.raises(AttributeError):
            config.checksum = "new"


class TestSDKConfig:
    def test_defaults(self):
        cfg = SDKConfig(
            server_url="http://localhost:8000/api/v1",
            scope=ScopeParams(service_name="payment-svc"),
        )
        assert cfg.poll_interval_sec == 30.0
        assert cfg.request_timeout_sec == 10.0
        assert cfg.max_backoff_sec == 300.0
        assert cfg.base_backoff_sec == 1.0
        assert cfg.backoff_multiplier == 2.0
        assert cfg.backoff_jitter is True
        assert cfg.retry_on_status == (500, 502, 503, 504)
        assert cfg.logger_name == "configsphere"
        assert cfg.auth_token is None

    def test_custom_values(self):
        cfg = SDKConfig(
            server_url="http://config:8000/api/v1",
            scope=ScopeParams(service_name="svc"),
            poll_interval_sec=5.0,
            auth_token="Bearer tok123",
        )
        assert cfg.poll_interval_sec == 5.0
        assert cfg.auth_token == "Bearer tok123"
