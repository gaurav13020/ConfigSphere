"""
Tests for model-level constraints and uniqueness rules.
"""

from django.db import IntegrityError
from django.test import TestCase

from apps.configs.models import ConfigItem
from common.constants import ScopeLevel


class TestConfigItemUniqueConstraint(TestCase):

    def test_duplicate_key_at_same_scope_raises(self):
        ConfigItem.objects.create(
            key="timeout",
            scope_level=ScopeLevel.GLOBAL,
            global_name="default",
        )
        with self.assertRaises(IntegrityError):
            ConfigItem.objects.create(
                key="timeout",
                scope_level=ScopeLevel.GLOBAL,
                global_name="default",
            )

    def test_same_key_different_scope_level_allowed(self):
        ConfigItem.objects.create(
            key="timeout",
            scope_level=ScopeLevel.GLOBAL,
            global_name="default",
        )
        # Same key, different scope level — should not conflict
        item = ConfigItem.objects.create(
            key="timeout",
            scope_level=ScopeLevel.SERVICE,
            global_name="default",
            service_name="payment",
        )
        assert item.pk is not None

    def test_same_key_different_service_name_allowed(self):
        ConfigItem.objects.create(
            key="log_level",
            scope_level=ScopeLevel.SERVICE,
            service_name="svc-a",
        )
        item = ConfigItem.objects.create(
            key="log_level",
            scope_level=ScopeLevel.SERVICE,
            service_name="svc-b",
        )
        assert item.pk is not None
