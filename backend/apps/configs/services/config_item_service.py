from __future__ import annotations

from apps.audits.services import AuditService
from apps.schemas.models import SchemaDefinition
from common.constants import AuditEventType, ConfigItemStatus, ScopeLevel
from common.exceptions import ConflictError, NotFoundError
from ..models import ConfigItem


class ConfigItemService:
    """
    Manages lifecycle of ConfigItem entities.
    Scope field assignment is validated and enforced here, not in the model.
    """

    SCOPE_REQUIRED_FIELDS = {
        ScopeLevel.GLOBAL: [],
        ScopeLevel.REGION: ["region_name"],
        ScopeLevel.GROUP: ["region_name", "group_name"],
        ScopeLevel.SERVICE: ["service_name"],
    }

    @staticmethod
    def create(
        key: str,
        scope_level: str,
        global_name: str = "default",
        region_name: str | None = None,
        group_name: str | None = None,
        service_name: str | None = None,
        schema_id: int | None = None,
        description: str = "",
        created_by: str | None = None,
    ) -> ConfigItem:
        ConfigItemService._validate_scope_fields(
            scope_level, region_name, group_name, service_name
        )

        schema = None
        if schema_id is not None:
            try:
                schema = SchemaDefinition.objects.get(pk=schema_id)
            except SchemaDefinition.DoesNotExist:
                raise NotFoundError(f"SchemaDefinition with id={schema_id} does not exist.")

        # Normalise: store "" (not None) so the UNIQUE constraint fires correctly
        region_name = region_name or ""
        group_name = group_name or ""
        service_name = service_name or ""

        # Check uniqueness before insert for a cleaner error message
        if ConfigItem.objects.filter(
            key=key,
            scope_level=scope_level,
            global_name=global_name,
            region_name=region_name,
            group_name=group_name,
            service_name=service_name,
        ).exists():
            raise ConflictError(
                f"A ConfigItem with key='{key}' already exists at this scope."
            )

        item = ConfigItem.objects.create(
            key=key,
            scope_level=scope_level,
            global_name=global_name,
            region_name=region_name,
            group_name=group_name,
            service_name=service_name,
            schema=schema,
            description=description,
            created_by=created_by,
            status=ConfigItemStatus.ACTIVE,
        )

        AuditService.record(
            event_type=AuditEventType.CONFIG_ITEM_CREATED,
            actor=created_by,
            config_item_id=item.id,
            metadata={"key": key, "scope_level": scope_level},
        )

        return item

    @staticmethod
    def _validate_scope_fields(
        scope_level: str,
        region_name: str | None,
        group_name: str | None,
        service_name: str | None,
    ) -> None:
        if scope_level == ScopeLevel.REGION and not region_name:
            raise ValueError("region_name is required for scope_level=region.")
        if scope_level == ScopeLevel.GROUP and not (region_name and group_name):
            raise ValueError("region_name and group_name are required for scope_level=group.")
        if scope_level == ScopeLevel.SERVICE and not service_name:
            raise ValueError("service_name is required for scope_level=service.")
