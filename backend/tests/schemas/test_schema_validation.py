"""
Tests for SchemaValidationService and schema-gated ConfigVersion creation.
"""

from django.test import TestCase

from apps.configs.services import ConfigItemService, ConfigVersionService, SchemaValidationService
from apps.schemas.models import SchemaDefinition
from apps.schemas.services import SchemaService
from common.constants import ScopeLevel, VersionStatus
from common.exceptions import ValidationError as DomainValidationError


VALID_SCHEMA = {
    "type": "object",
    "properties": {
        "timeout": {"type": "integer", "minimum": 1},
        "retries": {"type": "integer"},
    },
    "required": ["timeout"],
    "additionalProperties": False,
}


class TestSchemaValidationService(TestCase):

    def setUp(self):
        self.schema = SchemaDefinition.objects.create(
            name="service-config-v1",
            schema_json=VALID_SCHEMA,
        )

    def test_valid_payload_passes(self):
        valid, error = SchemaValidationService.validate(
            {"timeout": 30, "retries": 3}, self.schema
        )
        assert valid is True
        assert error == ""

    def test_missing_required_field_fails(self):
        valid, error = SchemaValidationService.validate({"retries": 3}, self.schema)
        assert valid is False
        assert "timeout" in error

    def test_wrong_type_fails(self):
        valid, error = SchemaValidationService.validate({"timeout": "thirty"}, self.schema)
        assert valid is False
        assert error != ""

    def test_additional_property_fails(self):
        valid, error = SchemaValidationService.validate(
            {"timeout": 30, "unknown_field": True}, self.schema
        )
        assert valid is False

    def test_assert_valid_raises_on_failure(self):
        with self.assertRaises(DomainValidationError):
            SchemaValidationService.assert_valid({"retries": 3}, self.schema)

    def test_assert_valid_passes_silently(self):
        # Should not raise
        SchemaValidationService.assert_valid({"timeout": 10}, self.schema)


class TestSchemaGatedVersionCreation(TestCase):
    """
    Verify that ConfigVersionService respects schema validation on creation.
    """

    def setUp(self):
        self.schema = SchemaService.create("svc-schema", VALID_SCHEMA)
        self.item = ConfigItemService.create(
            key="svc_config",
            scope_level=ScopeLevel.SERVICE,
            service_name="checkout",
            schema_id=self.schema.id,
        )

    def test_valid_payload_creates_validated_version(self):
        version = ConfigVersionService.create(
            config_item_id=self.item.id,
            payload={"timeout": 30},
        )
        assert version.status == VersionStatus.VALIDATED
        assert version.validation_error == ""

    def test_invalid_payload_creates_draft_version_with_error(self):
        version = ConfigVersionService.create(
            config_item_id=self.item.id,
            payload={"retries": 3},  # missing required 'timeout'
        )
        assert version.status == VersionStatus.DRAFT
        assert version.validation_error != ""
        assert "timeout" in version.validation_error

    def test_draft_version_cannot_be_activated(self):
        from common.exceptions import ActivationError
        from apps.configs.services import ActivationService
        version = ConfigVersionService.create(
            config_item_id=self.item.id,
            payload={"retries": 3},
        )
        assert version.status == VersionStatus.DRAFT
        with self.assertRaises(ActivationError):
            ActivationService.activate(version.id)

    def test_no_schema_item_creates_validated_version_directly(self):
        item_no_schema = ConfigItemService.create(
            key="free_config",
            scope_level=ScopeLevel.GLOBAL,
        )
        version = ConfigVersionService.create(
            config_item_id=item_no_schema.id,
            payload={"anything": "goes"},
        )
        assert version.status == VersionStatus.VALIDATED
