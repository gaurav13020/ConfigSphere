from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from configsphere_shared.cache import TwoTierCache
from configsphere_shared.config_payloads import ConfigPayloadStore
from configsphere_shared.models import ConfigNode, ConfigNodeVersion, Service, ServiceApiKey
from configsphere_shared.security import (
    AuthenticatedUser,
    DeliveryApiPrincipal,
    SERVICE_API_KEY_PREFIX,
    get_current_user,
    hash_service_api_key_token,
)

from app.db import get_db, get_redis_client
from app.invalidation_consumer import run_invalidation_consumer

_L1_TTL = int(os.getenv("CACHE_L1_TTL_SECONDS", "600"))
_L2_TTL = int(os.getenv("CACHE_L2_TTL_SECONDS", "1800"))

_cache: TwoTierCache | None = None


def _get_cache() -> TwoTierCache:
    assert _cache is not None, "Cache not initialised — lifespan not running"
    return _cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cache
    _cache = TwoTierCache(get_redis_client(), l1_ttl_seconds=_L1_TTL, l2_ttl_seconds=_L2_TTL)
    task = asyncio.create_task(run_invalidation_consumer(_cache))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="ConfigSphere V2 Delivery", lifespan=lifespan)
payload_store = ConfigPayloadStore()

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3001,http://127.0.0.1:3001").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _normalize_path(path: str) -> str:
    value = path.strip()
    if not value.startswith("/"):
        value = f"/{value}"
    return value.rstrip("/") or "/"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _resolve_delivery_principal(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
    x_config_token: str | None = Header(default=None),
    x_dev_user: str | None = Header(default=None),
    x_dev_name: str | None = Header(default=None),
) -> AuthenticatedUser | DeliveryApiPrincipal:
    token = x_config_token
    if not token and authorization and authorization.startswith("Bearer "):
        candidate = authorization.removeprefix("Bearer ").strip()
        if candidate.startswith(SERVICE_API_KEY_PREFIX):
            token = candidate

    if token:
        token_hash = hash_service_api_key_token(token)
        api_key = db.scalar(select(ServiceApiKey).where(ServiceApiKey.token_hash == token_hash))
        if not api_key or api_key.revoked_at is not None:
            raise HTTPException(status_code=401, detail="Invalid delivery API key")
        return DeliveryApiPrincipal(service_id=str(api_key.service_id), token_prefix=api_key.token_prefix)

    return get_current_user(authorization=authorization, x_dev_user=x_dev_user, x_dev_name=x_dev_name)


@app.get("/v1/config")
def get_config(
    service: str,
    path: str,
    db: Session = Depends(get_db),
    principal: AuthenticatedUser | DeliveryApiPrincipal = Depends(_resolve_delivery_principal),
    cache: TwoTierCache = Depends(_get_cache),
):
    normalized_path = _normalize_path(path)
    cache_key = f"delivery:config:{service}:{normalized_path}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    service_row = db.scalar(select(Service).where(Service.service_name == service))
    if not service_row:
        raise HTTPException(status_code=404, detail="Service not found")
    if isinstance(principal, DeliveryApiPrincipal) and principal.service_id != str(service_row.service_id):
        raise HTTPException(status_code=403, detail="API key is not allowed for this service")

    node = db.scalar(
        select(ConfigNode).where(
            ConfigNode.service_id == service_row.service_id,
            ConfigNode.path == normalized_path,
        )
    )
    if not node or not node.active_version_id:
        raise HTTPException(status_code=404, detail="Config node or active version not found")

    version = db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == node.active_version_id))
    if not version:
        raise HTTPException(status_code=404, detail="Active version not found")

    document = payload_store.get_document_by_id("NODE", str(node.config_node_id), version.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Config payload not found")

    response = {
        "serviceId": str(service_row.service_id),
        "serviceName": service_row.service_name,
        "configNodeId": str(node.config_node_id),
        "path": node.path,
        "versionId": str(version.version_id),
        "treeVersion": version.tree_version,
        "materializedConfig": document.get("materializedConfig", {}),
        "keyCount": document.get("keyCount", 0),
    }
    cache.set(cache_key, response)
    return response


@app.get("/v1/config/version")
def get_config_version(
    service: str,
    path: str,
    db: Session = Depends(get_db),
    principal: AuthenticatedUser | DeliveryApiPrincipal = Depends(_resolve_delivery_principal),
    cache: TwoTierCache = Depends(_get_cache),
):
    normalized_path = _normalize_path(path)
    cache_key = f"delivery:version:{service}:{normalized_path}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    service_row = db.scalar(select(Service).where(Service.service_name == service))
    if not service_row:
        raise HTTPException(status_code=404, detail="Service not found")
    if isinstance(principal, DeliveryApiPrincipal) and principal.service_id != str(service_row.service_id):
        raise HTTPException(status_code=403, detail="API key is not allowed for this service")

    node = db.scalar(
        select(ConfigNode).where(
            ConfigNode.service_id == service_row.service_id,
            ConfigNode.path == normalized_path,
        )
    )
    if not node or not node.active_version_id:
        raise HTTPException(status_code=404, detail="Config node or active version not found")

    version = db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == node.active_version_id))

    response = {
        "serviceName": service_row.service_name,
        "path": node.path,
        "versionId": str(version.version_id),
        "treeVersion": service_row.current_tree_version,
    }
    cache.set(cache_key, response)
    return response
