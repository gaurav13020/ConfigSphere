from __future__ import annotations

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


# ── Domain exceptions ────────────────────────────────────────────────────────

class ConfigSphereError(Exception):
    """Base for all domain-level errors."""


class ValidationError(ConfigSphereError):
    """Raised when a config payload fails schema validation."""

    def __init__(self, message: str, details: list | None = None):
        super().__init__(message)
        self.details = details or []


class ActivationError(ConfigSphereError):
    """Raised when a version cannot be activated in its current state."""


class NotFoundError(ConfigSphereError):
    """Raised when a required domain object does not exist."""


class ConflictError(ConfigSphereError):
    """Raised when an operation conflicts with existing state."""


# ── DRF exception handler ────────────────────────────────────────────────────

def custom_exception_handler(exc, context):
    """
    Translate domain exceptions into structured HTTP responses.
    Falls back to DRF's default handler for framework-level exceptions.
    """
    if isinstance(exc, ValidationError):
        return Response(
            {"error": "validation_failed", "message": str(exc), "details": exc.details},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    if isinstance(exc, ActivationError):
        return Response(
            {"error": "activation_failed", "message": str(exc)},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, NotFoundError):
        return Response(
            {"error": "not_found", "message": str(exc)},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, ConflictError):
        return Response(
            {"error": "conflict", "message": str(exc)},
            status=status.HTTP_409_CONFLICT,
        )

    return exception_handler(exc, context)
