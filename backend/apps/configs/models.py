from django.db import models

from apps.schemas.models import SchemaDefinition
from common.constants import ConfigItemStatus, ScopeLevel, VersionStatus


class ConfigItem(models.Model):
    """
    A logical configuration entity scoped to a specific level in the hierarchy.

    Scope identity is (scope_level, key, global_name, region_name, group_name, service_name).
    The DB-level unique constraint enforces at most one config item per key per concrete scope.

    Scope field convention:
      All scope fields use empty string ("") as the sentinel for "not applicable at this level".
      This enables a clean UNIQUE constraint across all backends (SQLite, PostgreSQL).
      NULL would make rows appear distinct even when semantically identical.

      scope_level=global   → global_name set, others are ""
      scope_level=region   → global_name + region_name set, others are ""
      scope_level=group    → global_name + region_name + group_name set, service_name is ""
      scope_level=service  → service_name set; global/region/group may also be set

    active_version is a direct FK to the currently active ConfigVersion.
    Kept explicit (not inferred) for O(1) resolution lookups.
    Updated atomically during activation.
    """

    key = models.CharField(max_length=255, db_index=True)
    scope_level = models.CharField(
        max_length=32, choices=ScopeLevel.CHOICES, db_index=True
    )

    # Scope fields — use "" (not NULL) as "not applicable" sentinel for uniqueness
    global_name = models.CharField(max_length=255, default="default")
    region_name = models.CharField(max_length=255, blank=True, default="")
    group_name = models.CharField(max_length=255, blank=True, default="")
    service_name = models.CharField(max_length=255, blank=True, default="")

    schema = models.ForeignKey(
        SchemaDefinition,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="config_items",
    )

    status = models.CharField(
        max_length=32,
        choices=ConfigItemStatus.CHOICES,
        default=ConfigItemStatus.ACTIVE,
        db_index=True,
    )

    # Set by activation service; null means no version is currently active
    active_version = models.OneToOneField(
        "ConfigVersion",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="active_for_item",
    )

    description = models.TextField(blank=True, default="")
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["key", "scope_level", "global_name", "region_name", "group_name", "service_name"],
                name="uq_config_item_scope_key",
            )
        ]
        indexes = [
            models.Index(fields=["scope_level", "service_name"]),
            models.Index(fields=["scope_level", "region_name"]),
        ]

    def __str__(self):
        return f"ConfigItem({self.key} @ {self.scope_level})"


class ConfigVersion(models.Model):
    """
    An immutable snapshot of a config payload for a given ConfigItem.

    Once created, payload and checksum MUST NOT change.
    Status transitions: draft → validated → active (→ archived on supersession).
    An item can have at most one active version at any time (enforced in service layer).
    """

    config_item = models.ForeignKey(
        ConfigItem,
        on_delete=models.CASCADE,
        related_name="versions",
    )
    version_number = models.PositiveIntegerField()

    payload = models.JSONField()
    checksum = models.CharField(max_length=64)

    status = models.CharField(
        max_length=32,
        choices=VersionStatus.CHOICES,
        default=VersionStatus.DRAFT,
        db_index=True,
    )

    validation_error = models.TextField(blank=True, default="")

    change_summary = models.TextField(blank=True, default="")
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["config_item", "version_number"],
                name="uq_config_version_number",
            )
        ]
        indexes = [
            models.Index(fields=["config_item", "status"]),
        ]
        ordering = ["-version_number"]

    def __str__(self):
        return f"ConfigVersion({self.config_item.key} v{self.version_number} [{self.status}])"
