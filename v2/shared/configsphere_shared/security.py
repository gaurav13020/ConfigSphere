from __future__ import annotations

import os
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any

from fastapi import Header, HTTPException, status


@dataclass
class AuthenticatedUser:
    subject: str
    email: str
    display_name: str


@dataclass
class DeliveryApiPrincipal:
    service_id: str
    token_prefix: str


def get_current_user(
    authorization: str | None = Header(default=None),
    x_dev_user: str | None = Header(default=None),
    x_dev_name: str | None = Header(default=None),
) -> AuthenticatedUser:
    dev_mode = os.getenv("AUTH_DEV_MODE", "true").lower() == "true"
    if dev_mode:
        email = x_dev_user or "dev-author@example.com"
        return AuthenticatedUser(
            subject=f"dev::{email}",
            email=email,
            display_name=x_dev_name or email.split("@")[0].replace(".", " ").title(),
        )

    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    # Full Keycloak JWT validation is intentionally lightweight in this slice.
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid bearer token")

    return AuthenticatedUser(subject=token, email=f"{token}@example.com", display_name="Keycloak User")


def build_display_name(payload: dict[str, Any]) -> str:
    return payload.get("name") or payload.get("preferred_username") or payload.get("email", "Unknown User")


SERVICE_API_KEY_PREFIX = "cfgsdk_"


def generate_service_api_key_token() -> str:
    return f"{SERVICE_API_KEY_PREFIX}{secrets.token_urlsafe(32)}"


def hash_service_api_key_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
