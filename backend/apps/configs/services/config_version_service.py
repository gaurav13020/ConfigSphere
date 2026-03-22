from __future__ import annotations

from apps.audits.services import AuditService
from common.constants import AuditEventType, VersionStatus
from common.exceptions import NotFoundError
from common.utils import compute_checksum
from ..models import ConfigItem, ConfigVersion
from .schema_validation_service import SchemaValidationService


class ConfigVersionService:
    """
    Creates new ConfigVersion records for a given ConfigItem.

    Validation strategy (deliberate design):
      - If the item has no schema: version is created as VALIDATED (no schema to check).
      - If the item has a schema and validation passes: version is VALIDATED.
      - If the item has a schema and validation fails: version is persisted as DRAFT
        with validation_error populated.

    Rationale: persist failures for traceability and audit. Operators can see
    what was submitted, correct it, and create a new version. Silently dropping
    failed attempts destroys auditability.
    """

    @staticmethod
    def create(
        config_item_id: int,
        payload: dict,
        change_summary: str = "",
        created_by: str | None = None,
    ) -> ConfigVersion:
        try:
            item = ConfigItem.objects.select_related("schema").get(pk=config_item_id)
        except ConfigItem.DoesNotExist:
            raise NotFoundError(f"ConfigItem with id={config_item_id} does not exist.")

        checksum = compute_checksum(payload)
        version_number = ConfigVersionService._next_version_number(item)

        validation_status = VersionStatus.VALIDATED
        validation_error = ""

        if item.schema is not None:
            valid, error_msg = SchemaValidationService.validate(payload, item.schema)
            if valid:
                AuditService.record(
                    event_type=AuditEventType.VALIDATION_PASSED,
                    actor=created_by,
                    config_item_id=item.id,
                    metadata={"version_number": version_number},
                )
            else:
                validation_status = VersionStatus.DRAFT
                validation_error = error_msg
                AuditService.record(
                    event_type=AuditEventType.VALIDATION_FAILED,
                    actor=created_by,
                    config_item_id=item.id,
                    metadata={"version_number": version_number, "error": error_msg},
                )

        version = ConfigVersion.objects.create(
            config_item=item,
            version_number=version_number,
            payload=payload,
            checksum=checksum,
            status=validation_status,
            validation_error=validation_error,
            change_summary=change_summary,
            created_by=created_by,
        )

        AuditService.record(
            event_type=AuditEventType.CONFIG_VERSION_CREATED,
            actor=created_by,
            config_item_id=item.id,
            config_version_id=version.id,
            metadata={
                "version_number": version_number,
                "status": validation_status,
                "checksum": checksum,
            },
        )

        return version

    @staticmethod
    def _next_version_number(item: ConfigItem) -> int:
        last = ConfigVersion.objects.filter(config_item=item).order_by("-version_number").first()
        return (last.version_number + 1) if last else 1
