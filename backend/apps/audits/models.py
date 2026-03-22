from django.db import models

from common.constants import AuditEventType


class AuditEvent(models.Model):
    """
    Append-only audit log. Never update or delete rows.

    Loosely coupled to configs via nullable string references
    so that audit data outlives any future model changes.
    FK references are also kept (nullable) for query convenience.
    """

    event_type = models.CharField(
        max_length=64,
        db_index=True,
        choices=[
            (v, v)
            for v in [
                AuditEventType.SCHEMA_CREATED,
                AuditEventType.CONFIG_ITEM_CREATED,
                AuditEventType.CONFIG_VERSION_CREATED,
                AuditEventType.VALIDATION_PASSED,
                AuditEventType.VALIDATION_FAILED,
                AuditEventType.VERSION_ACTIVATED,
                AuditEventType.VERSION_ARCHIVED,
                AuditEventType.RESOLVED_CONFIG_FETCHED,
            ]
        ],
    )

    # Who triggered this event. Will map to User FK once auth is added.
    actor = models.CharField(max_length=255, null=True, blank=True)

    # Loose references — do NOT use FK with CASCADE DELETE on audit events.
    # We want the audit trail to survive even if config objects are deleted.
    config_item_id_ref = models.BigIntegerField(null=True, blank=True, db_index=True)
    config_version_id_ref = models.BigIntegerField(null=True, blank=True, db_index=True)
    schema_id_ref = models.BigIntegerField(null=True, blank=True)

    # Flexible JSON bag for event-specific context
    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type", "created_at"]),
        ]

    def __str__(self):
        return f"AuditEvent({self.event_type}, {self.created_at})"
