"""
Tests for ActivationService.

Tests verify:
  - happy path activation
  - atomic archive of previous active version
  - ConfigItem.active_version pointer update
  - rejection of draft/archived/already-active versions
"""

from django.test import TestCase

from apps.configs.models import ConfigItem, ConfigVersion
from apps.configs.services import ActivationService, ConfigItemService, ConfigVersionService
from common.constants import ScopeLevel, VersionStatus
from common.exceptions import ActivationError


class TestActivationService(TestCase):

    def setUp(self):
        self.item = ConfigItemService.create(
            key="database_url",
            scope_level=ScopeLevel.GLOBAL,
        )

    def _make_version(self, payload=None):
        return ConfigVersionService.create(
            config_item_id=self.item.id,
            payload=payload or {"url": "postgres://localhost/db"},
        )

    def test_activating_validated_version_succeeds(self):
        version = self._make_version()
        assert version.status == VersionStatus.VALIDATED

        activated = ActivationService.activate(version.id)
        assert activated.status == VersionStatus.ACTIVE

    def test_config_item_active_version_pointer_updated(self):
        version = self._make_version()
        ActivationService.activate(version.id)

        self.item.refresh_from_db()
        assert self.item.active_version_id == version.id

    def test_previous_active_version_is_archived(self):
        v1 = self._make_version({"url": "postgres://old"})
        ActivationService.activate(v1.id)

        v2 = self._make_version({"url": "postgres://new"})
        ActivationService.activate(v2.id)

        v1.refresh_from_db()
        assert v1.status == VersionStatus.ARCHIVED

    def test_only_one_version_active_at_a_time(self):
        v1 = self._make_version()
        ActivationService.activate(v1.id)

        v2 = self._make_version()
        ActivationService.activate(v2.id)

        active_count = ConfigVersion.objects.filter(
            config_item=self.item, status=VersionStatus.ACTIVE
        ).count()
        assert active_count == 1

    def test_activating_already_active_version_raises(self):
        version = self._make_version()
        ActivationService.activate(version.id)

        with self.assertRaises(ActivationError):
            ActivationService.activate(version.id)

    def test_activating_archived_version_raises(self):
        v1 = self._make_version()
        ActivationService.activate(v1.id)

        v2 = self._make_version()
        ActivationService.activate(v2.id)  # archives v1

        with self.assertRaises(ActivationError):
            ActivationService.activate(v1.id)  # v1 is now archived

    def test_activating_nonexistent_version_raises(self):
        from common.exceptions import NotFoundError
        with self.assertRaises(NotFoundError):
            ActivationService.activate(version_id=99999)
