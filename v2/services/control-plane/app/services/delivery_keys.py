from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from configsphere_shared.models import Service, ServiceApiKey
from configsphere_shared.security import generate_service_api_key_token, hash_service_api_key_token


def create_service_api_key(
    db: Session,
    *,
    service: Service,
    key_name: str,
    created_by: uuid.UUID,
) -> tuple[ServiceApiKey, str]:
    normalized_name = key_name.strip()
    if not normalized_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Key name is required")

    plain_token = generate_service_api_key_token()
    token_hash = hash_service_api_key_token(plain_token)
    api_key = ServiceApiKey(
        service_id=service.service_id,
        key_name=normalized_name,
        token_prefix=plain_token[:16],
        token_hash=token_hash,
        created_by=created_by,
    )
    db.add(api_key)
    db.flush()
    return api_key, plain_token


def list_service_api_keys(db: Session, service_id: uuid.UUID) -> list[ServiceApiKey]:
    return db.scalars(
        select(ServiceApiKey)
        .where(ServiceApiKey.service_id == service_id)
        .order_by(ServiceApiKey.created_at.desc())
    ).all()


def revoke_service_api_key(db: Session, api_key: ServiceApiKey) -> ServiceApiKey:
    if api_key.revoked_at is None:
        api_key.revoked_at = datetime.utcnow()
        db.add(api_key)
    return api_key
