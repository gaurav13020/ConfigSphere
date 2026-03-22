"""
Tests verifying that audit events are recorded at all critical operations.
"""

from django.test import TestCase

from apps.audits.models import AuditEvent
from apps.configs.services import ActivationService, ConfigItemService, ConfigVersionService
from apps.schemas.services import SchemaService
from common.constants import AuditEventType, ScopeLevel


class TestAuditEventRecording(TestCase):

    def test_schema_creation_recorded(self):
        SchemaService.create("test-schema", {"type": "object"})
        assert AuditEvent.objects.filter(event_type=AuditEventType.SCHEMA_CREATED).exists()

    def test_config_item_creation_recorded(self):
        ConfigItemService.create(key="k", scope_level=ScopeLevel.GLOBAL)
        assert AuditEvent.objects.filter(event_type=AuditEventType.CONFIG_ITEM_CREATED).exists()

    def test_config_version_creation_recorded(self):
        item = ConfigItemService.create(key="v", scope_level=ScopeLevel.GLOBAL)
        ConfigVersionService.create(config_item_id=item.id, payload={"x": 1})
        assert AuditEvent.objects.filter(event_type=AuditEventType.CONFIG_VERSION_CREATED).exists()

    def test_activation_recorded(self):
        item = ConfigItemService.create(key="act", scope_level=ScopeLevel.GLOBAL)
        version = ConfigVersionService.create(config_item_id=item.id, payload={"x": 1})
        ActivationService.activate(version.id)
        assert AuditEvent.objects.filter(event_type=AuditEventType.VERSION_ACTIVATED).exists()

    def test_previous_version_archive_recorded(self):
        item = ConfigItemService.create(key="arch", scope_level=ScopeLevel.GLOBAL)
        v1 = ConfigVersionService.create(config_item_id=item.id, payload={"a": 1})
        ActivationService.activate(v1.id)

        v2 = ConfigVersionService.create(config_item_id=item.id, payload={"a": 2})
        ActivationService.activate(v2.id)

        assert AuditEvent.objects.filter(event_type=AuditEventType.VERSION_ARCHIVED).exists()

    def test_validation_failed_recorded(self):
        schema = SchemaService.create(
            "strict-schema",
            {"type": "object", "required": ["required_key"], "properties": {"required_key": {"type": "string"}}},
        )
        item = ConfigItemService.create(
            key="validated_cfg",
            scope_level=ScopeLevel.GLOBAL,
            schema_id=schema.id,
        )
        # Missing required_key → validation failure
        ConfigVersionService.create(config_item_id=item.id, payload={"other": "value"})
        assert AuditEvent.objects.filter(event_type=AuditEventType.VALIDATION_FAILED).exists()
