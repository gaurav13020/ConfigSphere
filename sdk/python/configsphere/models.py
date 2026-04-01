"""Data classes for the ConfigSphere SDK."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ScopeParams:
    """Scope parameters identifying which config hierarchy to resolve."""

    service_name: str
    region_name: str | None = None
    group_name: str | None = None
    global_name: str = "default"


@dataclass(frozen=True)
class ConfigLayer:
    """A single layer that contributed to the resolved configuration."""

    scope_level: str
    config_item_id: int
    config_version_id: int
    version_number: int
    checksum: str
    key: str


@dataclass(frozen=True)
class ResolvedConfig:
    """A snapshot of the resolved configuration from the server."""

    payload: dict[str, Any]
    checksum: str
    layers: tuple[ConfigLayer, ...]
    scope_params: ScopeParams
    fetched_at: datetime


@dataclass(frozen=True)
class SDKConfig:
    """Configuration for the ConfigSphere SDK client."""

    server_url: str
    scope: ScopeParams
    poll_interval_sec: float = 30.0
    request_timeout_sec: float = 10.0
    max_backoff_sec: float = 300.0
    base_backoff_sec: float = 1.0
    backoff_multiplier: float = 2.0
    backoff_jitter: bool = True
    retry_on_status: tuple[int, ...] = (500, 502, 503, 504)
    logger_name: str = "configsphere"
    auth_token: str | None = None
