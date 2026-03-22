from __future__ import annotations

from django.db import transaction

from apps.audits.services import AuditService
from common.constants import AuditEventType, VersionStatus
from common.exceptions import ActivationError, NotFoundError
from ..models import ConfigItem, ConfigVersion


class ActivationService:
    """
    Handles the atomic transition of a ConfigVersion to ACTIVE status.

    Invariants enforced:
      1. Only VALIDATED versions can be activated (not DRAFT or already ACTIVE/ARCHIVED).
      2. At most one ACTIVE version per ConfigItem at any time.
      3. The previous active version is atomically ARCHIVED in the same transaction.
      4. ConfigItem.active_version FK is updated atomically.

    All of this happens in a single DB transaction. The caller's view layer
    has ATOMIC_REQUESTS=True but we use an explicit transaction here because
    this is a critical multi-row update that must never be partial.
    """

    @staticmethod
    @transaction.atomic
    def activate(version_id: int, actor: str | None = None) -> ConfigVersion:
        # Lock the version row to prevent concurrent activations
        try:
            version = ConfigVersion.objects.select_for_update().select_related(
                "config_item"
            ).get(pk=version_id)
        except ConfigVersion.DoesNotExist:
            raise NotFoundError(f"ConfigVersion with id={version_id} does not exist.")

        if version.status == VersionStatus.ACTIVE:
            raise ActivationError(f"Version {version_id} is already active.")

        if version.status == VersionStatus.ARCHIVED:
            raise ActivationError(
                f"Version {version_id} is archived and cannot be re-activated. "
                "Create a new version instead."
            )

        if version.status == VersionStatus.DRAFT:
            raise ActivationError(
                f"Version {version_id} is in draft state (validation failed). "
                "Fix the payload and create a new version."
            )

        # At this point status must be VALIDATED
        item = version.config_item

        # Archive the currently active version if one exists
        if item.active_version_id is not None:
            prev_version_id = item.active_version_id
            ConfigVersion.objects.filter(pk=prev_version_id).update(
                status=VersionStatus.ARCHIVED
            )
            AuditService.record(
                event_type=AuditEventType.VERSION_ARCHIVED,
                actor=actor,
                config_item_id=item.id,
                config_version_id=prev_version_id,
                metadata={"superseded_by": version_id},
            )

        # Activate the new version
        version.status = VersionStatus.ACTIVE
        version.save(update_fields=["status"])

        # Update the pointer on ConfigItem
        ConfigItem.objects.filter(pk=item.pk).update(active_version=version)

        AuditService.record(
            event_type=AuditEventType.VERSION_ACTIVATED,
            actor=actor,
            config_item_id=item.id,
            config_version_id=version.id,
            metadata={
                "version_number": version.version_number,
                "checksum": version.checksum,
            },
        )

        version.refresh_from_db()
        return version
