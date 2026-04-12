from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class DeliveryVersionSnapshot:
    version_id: str
    tree_version: int


@dataclass
class DeliveryConfigSnapshot:
    version_id: str
    tree_version: int
    materialized_config: dict[str, str]


class ConfigDeliveryClient:
    def __init__(self, *, base_url: str, service_name: str, path: str, token: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
        self.path = path
        self.token = token
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        return {"X-Config-Token": self.token}

    async def fetch_version(self) -> DeliveryVersionSnapshot:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                f"{self.base_url}/v1/config/version",
                params={"service": self.service_name, "path": self.path},
                headers=self._headers(),
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return DeliveryVersionSnapshot(
                version_id=str(payload["versionId"]),
                tree_version=int(payload["treeVersion"]),
            )

    async def fetch_config(self) -> DeliveryConfigSnapshot:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                f"{self.base_url}/v1/config",
                params={"service": self.service_name, "path": self.path},
                headers=self._headers(),
            )
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
            return DeliveryConfigSnapshot(
                version_id=str(payload["versionId"]),
                tree_version=int(payload["treeVersion"]),
                materialized_config=dict(payload.get("materializedConfig", {})),
            )
