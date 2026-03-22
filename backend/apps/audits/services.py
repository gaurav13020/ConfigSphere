from __future__ import annotations

import logging

from .models import AuditEvent

logger = logging.getLogger(__name__)


class AuditService:
    """
    Thin service wrapping AuditEvent creation.
    All business logic layers call this; it never calls back into them.
    """

    @staticmethod
    def record(
        event_type: str,
        actor: str | None = None,
        config_item_id: int | None = None,
        config_version_id: int | None = None,
        schema_id: int | None = None,
        metadata: dict | None = None,
    ) -> AuditEvent:
        event = AuditEvent.objects.create(
            event_type=event_type,
            actor=actor,
            config_item_id_ref=config_item_id,
            config_version_id_ref=config_version_id,
            schema_id_ref=schema_id,
            metadata=metadata or {},
        )
        logger.debug("Audit event recorded: %s (id=%s)", event_type, event.id)
        return event
