from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from configsphere_shared.config_payloads import ConfigPayloadStore
from configsphere_shared.constants import ACTIVE_VERSION, VersionStatus
from configsphere_shared.models import ConfigNode, ConfigNodeVersion, Service


def _normalize_path(path: str) -> str:
    value = path.strip()
    if not value.startswith("/"):
        value = f"/{value}"
    return value.rstrip("/") or "/"


def _validate_payload(service: Service, payload: dict[str, str]) -> None:
    if len(payload) > service.max_keys_per_node:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Config exceeds max key count")
    for key, value in payload.items():
        if len(value) > service.max_value_size:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Value for {key} exceeds max size")


def create_service(db: Session, service_name: str, service_type, owner_team: str | None) -> Service:
    service = Service(service_name=service_name, service_type=service_type, owner_team=owner_team)
    db.add(service)
    db.flush()
    return service


def create_root_node(
    db: Session,
    payload_store: ConfigPayloadStore,
    service: Service,
    path: str,
    base_config: dict[str, str],
    created_by: uuid.UUID | None,
) -> ConfigNode:
    path = _normalize_path(path)
    if service.node_count > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Root node already exists for service")
    if path.count("/") - 1 >= service.max_depth:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path exceeds max depth")
    _validate_payload(service, base_config)

    node = ConfigNode(service_id=service.service_id, path=path, depth=1)
    db.add(node)
    db.flush()

    document_id = payload_store.put_document(
        "NODE",
        str(node.config_node_id),
        "1",
        {
            "documentType": ACTIVE_VERSION,
            "serviceId": str(service.service_id),
            "configNodeId": str(node.config_node_id),
            "path": path,
            "materializedConfig": base_config,
            "localOverrides": base_config,
            "overrideKeys": sorted(base_config.keys()),
            "keyCount": len(base_config),
            "createdAt": datetime.utcnow().isoformat(),
        },
    )
    version = ConfigNodeVersion(
        config_node_id=node.config_node_id,
        service_id=service.service_id,
        tree_version=service.current_tree_version,
        document_id=document_id,
        version_status=VersionStatus.ACTIVE,
        created_by=created_by,
    )
    db.add(version)
    db.flush()
    node.active_version_id = version.version_id
    service.node_count = 1
    db.add_all([node, service])
    return node


def create_child_node(
    db: Session,
    payload_store: ConfigPayloadStore,
    service: Service,
    parent: ConfigNode,
    segment: str,
    created_by: uuid.UUID | None,
) -> ConfigNode:
    if service.node_count >= service.max_nodes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service reached max node count")
    if not segment or "/" in segment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Segment must be a non-empty single path segment")

    path = f"{parent.path.rstrip('/')}/{segment}"
    depth = parent.depth + 1
    if depth > service.max_depth:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Child exceeds max depth")

    existing = db.scalar(select(ConfigNode).where(ConfigNode.service_id == service.service_id, ConfigNode.path == path))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Node path already exists")

    if not parent.active_version_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent has no active version")

    version = db.scalar(select(ConfigNodeVersion).where(ConfigNodeVersion.version_id == parent.active_version_id))
    parent_doc = payload_store.get_document_by_id("NODE", str(parent.config_node_id), version.document_id)
    materialized = dict(parent_doc["materializedConfig"])

    node = ConfigNode(
        service_id=service.service_id,
        parent_config_node_id=parent.config_node_id,
        path=path,
        depth=depth,
    )
    db.add(node)
    db.flush()

    document_id = payload_store.put_document(
        "NODE",
        str(node.config_node_id),
        "1",
        {
            "documentType": ACTIVE_VERSION,
            "serviceId": str(service.service_id),
            "configNodeId": str(node.config_node_id),
            "path": path,
            "materializedConfig": materialized,
            "localOverrides": {},
            "overrideKeys": [],
            "keyCount": len(materialized),
            "createdAt": datetime.utcnow().isoformat(),
        },
    )
    node_version = ConfigNodeVersion(
        config_node_id=node.config_node_id,
        service_id=service.service_id,
        tree_version=service.current_tree_version,
        document_id=document_id,
        version_status=VersionStatus.ACTIVE,
        created_by=created_by,
    )
    db.add(node_version)
    db.flush()
    node.active_version_id = node_version.version_id
    service.node_count += 1
    db.add_all([node, service])
    return node

