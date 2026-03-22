"""
Tests for HierarchyResolutionService — the core of the system.

Test strategy:
  - Use Django's TestCase (database-backed) because resolution depends on DB state.
  - Create config items + versions + activate them, then assert resolution output.
  - Each test sets up its own isolated scope to avoid cross-test interference.
"""

import pytest
from django.test import TestCase

from apps.configs.models import ConfigItem, ConfigVersion
from apps.configs.services import (
    ActivationService,
    ConfigItemService,
    ConfigVersionService,
    HierarchyResolutionService,
)
from common.constants import ScopeLevel


class TestHierarchyResolutionService(TestCase):

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _create_active_item(self, key, scope_level, payload, **scope_kwargs):
        """Create a ConfigItem, add a version, activate it. Return (item, version)."""
        item = ConfigItemService.create(key=key, scope_level=scope_level, **scope_kwargs)
        version = ConfigVersionService.create(config_item_id=item.id, payload=payload)
        version = ActivationService.activate(version_id=version.id)
        item.refresh_from_db()
        return item, version

    # ── Basic resolution ─────────────────────────────────────────────────────

    def test_resolves_global_config_only(self):
        self._create_active_item(
            key="timeout", scope_level=ScopeLevel.GLOBAL, payload={"timeout": 30}
        )
        result = HierarchyResolutionService.resolve(global_name="default")
        assert result.payload["timeout"] == 30
        assert len(result.layers) == 1
        assert result.layers[0].scope_level == ScopeLevel.GLOBAL

    def test_service_overrides_global(self):
        self._create_active_item(
            key="timeout", scope_level=ScopeLevel.GLOBAL, payload={"timeout": 30}
        )
        self._create_active_item(
            key="timeout",
            scope_level=ScopeLevel.SERVICE,
            payload={"timeout": 5},
            service_name="payment",
        )
        result = HierarchyResolutionService.resolve(service_name="payment")
        assert result.payload["timeout"] == 5

    def test_region_overrides_global(self):
        self._create_active_item(
            key="log_level", scope_level=ScopeLevel.GLOBAL, payload={"log_level": "INFO"}
        )
        self._create_active_item(
            key="log_level",
            scope_level=ScopeLevel.REGION,
            payload={"log_level": "DEBUG"},
            region_name="us-west",
        )
        result = HierarchyResolutionService.resolve(region_name="us-west")
        assert result.payload["log_level"] == "DEBUG"

    def test_service_overrides_region_overrides_global(self):
        """Full 3-level hierarchy: global < region < service."""
        self._create_active_item(
            key="log_level", scope_level=ScopeLevel.GLOBAL, payload={"log_level": "INFO"}
        )
        self._create_active_item(
            key="log_level",
            scope_level=ScopeLevel.REGION,
            payload={"log_level": "WARN"},
            region_name="eu-central",
        )
        self._create_active_item(
            key="log_level",
            scope_level=ScopeLevel.SERVICE,
            payload={"log_level": "ERROR"},
            service_name="billing",
        )

        result = HierarchyResolutionService.resolve(
            service_name="billing", region_name="eu-central"
        )
        assert result.payload["log_level"] == "ERROR"

    def test_merge_combines_disjoint_keys(self):
        """Keys from different scopes all appear in the merged payload."""
        self._create_active_item(
            key="global_settings",
            scope_level=ScopeLevel.GLOBAL,
            payload={"timeout": 30, "retry": 3},
        )
        self._create_active_item(
            key="service_settings",
            scope_level=ScopeLevel.SERVICE,
            payload={"max_connections": 100},
            service_name="orders",
        )
        result = HierarchyResolutionService.resolve(service_name="orders")
        assert result.payload["timeout"] == 30
        assert result.payload["retry"] == 3
        assert result.payload["max_connections"] == 100

    def test_no_active_versions_returns_empty_payload(self):
        """Resolution for a scope with no active config returns empty payload cleanly."""
        result = HierarchyResolutionService.resolve(service_name="ghost-service")
        assert result.payload == {}
        assert result.layers == []
        assert result.checksum is not None  # checksum of {} is still valid

    def test_inactive_item_excluded_from_resolution(self):
        """Items with status=inactive should not appear in resolved config."""
        item, _ = self._create_active_item(
            key="timeout", scope_level=ScopeLevel.GLOBAL, payload={"timeout": 30}
        )
        # Deactivate the item
        ConfigItem.objects.filter(pk=item.pk).update(status="inactive")

        result = HierarchyResolutionService.resolve(global_name="default")
        assert "timeout" not in result.payload

    def test_draft_version_not_included(self):
        """A version in draft state (failed validation) must not be resolved."""
        item = ConfigItemService.create(
            key="feature_flags",
            scope_level=ScopeLevel.GLOBAL,
        )
        # Create but do NOT activate — stays draft
        ConfigVersionService.create(config_item_id=item.id, payload={"flag": True})

        result = HierarchyResolutionService.resolve(global_name="default")
        assert "flag" not in result.payload

    def test_layer_metadata_is_accurate(self):
        """ResolvedLayer metadata must reference correct version and item IDs."""
        item, version = self._create_active_item(
            key="app_config",
            scope_level=ScopeLevel.SERVICE,
            payload={"debug": False},
            service_name="api-gateway",
        )
        result = HierarchyResolutionService.resolve(service_name="api-gateway")
        assert len(result.layers) == 1
        layer = result.layers[0]
        assert layer.config_item_id == item.id
        assert layer.config_version_id == version.id
        assert layer.version_number == version.version_number
        assert layer.checksum == version.checksum

    def test_checksum_is_deterministic(self):
        """Same effective config must always produce the same checksum."""
        self._create_active_item(
            key="cfg",
            scope_level=ScopeLevel.GLOBAL,
            payload={"a": 1, "b": 2},
        )
        result1 = HierarchyResolutionService.resolve(global_name="default")
        result2 = HierarchyResolutionService.resolve(global_name="default")
        assert result1.checksum == result2.checksum

    def test_group_overrides_region(self):
        """Group scope should override region when both are present."""
        self._create_active_item(
            key="rate_limit",
            scope_level=ScopeLevel.REGION,
            payload={"rate_limit": 1000},
            region_name="ap-south",
        )
        self._create_active_item(
            key="rate_limit",
            scope_level=ScopeLevel.GROUP,
            payload={"rate_limit": 500},
            region_name="ap-south",
            group_name="payment-team",
        )
        result = HierarchyResolutionService.resolve(
            region_name="ap-south", group_name="payment-team"
        )
        assert result.payload["rate_limit"] == 500

    def test_scope_isolation_across_services(self):
        """Service A config must not bleed into Service B resolution."""
        self._create_active_item(
            key="feature_x",
            scope_level=ScopeLevel.SERVICE,
            payload={"feature_x": True},
            service_name="service-a",
        )
        result = HierarchyResolutionService.resolve(service_name="service-b")
        assert "feature_x" not in result.payload
