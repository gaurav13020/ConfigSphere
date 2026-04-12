from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime

from fastapi import FastAPI

from configsphere_shared.sdk import ConfigDeliveryClient


def utcnow_iso() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class InstanceState:
    instance_id: str
    instance_name: str
    service_alias: str
    delivery_service_name: str
    path: str
    status: str = "idle"
    version_id: str | None = None
    tree_version: int | None = None
    config: dict[str, str] | None = None
    last_poll_at: str | None = None
    last_update_at: str | None = None
    error_message: str | None = None


SERVICE_ALIAS = os.getenv("DEMO_SERVICE_ALIAS", "payments-demo-01")
DELIVERY_SERVICE_NAME = os.getenv("DELIVERY_SERVICE_NAME", "payments")
CONFIG_PATH = os.getenv("CONFIG_PATH", "/global/us-east-1")
CONFIG_TOKEN = os.getenv("CONFIG_TOKEN", "")
INSTANCE_COUNT = int(os.getenv("INSTANCE_COUNT", "11"))
INSTANCE_PREFIX = os.getenv("INSTANCE_PREFIX", SERVICE_ALIAS)
POLL_INTERVAL_SECONDS = float(os.getenv("POLL_INTERVAL_SECONDS", "4"))
DELIVERY_BASE_URL = os.getenv("DELIVERY_BASE_URL", "http://host.docker.internal:8101")

INSTANCE_STATES = [
    InstanceState(
        instance_id=f"{SERVICE_ALIAS}-{index}",
        instance_name=f"{INSTANCE_PREFIX}-{index}",
        service_alias=SERVICE_ALIAS,
        delivery_service_name=DELIVERY_SERVICE_NAME,
        path=CONFIG_PATH,
    )
    for index in range(1, INSTANCE_COUNT + 1)
]


async def refresh_instance(state: InstanceState) -> None:
    client = ConfigDeliveryClient(
        base_url=DELIVERY_BASE_URL,
        service_name=DELIVERY_SERVICE_NAME,
        path=state.path,
        token=CONFIG_TOKEN,
    )
    state.last_poll_at = utcnow_iso()
    try:
        version = await client.fetch_version()
        if state.version_id != version.version_id:
            config = await client.fetch_config()
            state.version_id = config.version_id
            state.tree_version = config.tree_version
            state.config = config.materialized_config
            state.last_update_at = utcnow_iso()
        else:
            state.tree_version = version.tree_version
        state.status = "healthy"
        state.error_message = None
    except Exception as exc:  # noqa: BLE001
        state.status = "error"
        state.error_message = str(exc)


async def poll_instance(state: InstanceState) -> None:
    while True:
        await refresh_instance(state)
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    tasks = [asyncio.create_task(poll_instance(state)) for state in INSTANCE_STATES]
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(title=f"{SERVICE_ALIAS} demo service", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config")
def config_snapshot() -> dict:
    return {
        "serviceAlias": SERVICE_ALIAS,
        "deliveryServiceName": DELIVERY_SERVICE_NAME,
        "instanceCount": len(INSTANCE_STATES),
        "polledPath": CONFIG_PATH,
        "instances": [asdict(state) for state in INSTANCE_STATES],
    }


@app.post("/refresh")
async def refresh_snapshot() -> dict:
    await asyncio.gather(*(refresh_instance(state) for state in INSTANCE_STATES))
    return config_snapshot()
