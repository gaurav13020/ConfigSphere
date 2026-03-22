import jsonschema
import jsonschema.exceptions

from common.constants import AuditEventType
from common.exceptions import ValidationError as DomainValidationError
from .models import SchemaDefinition


class SchemaService:
    @staticmethod
    def create(name: str, schema_json: dict, description: str = "") -> SchemaDefinition:
        """
        Validate that schema_json is itself a valid JSON Schema meta-schema,
        then persist and audit.
        Audit is recorded here (service layer) so it fires regardless of caller.
        """
        SchemaService._assert_valid_meta_schema(schema_json)
        schema = SchemaDefinition.objects.create(
            name=name,
            schema_json=schema_json,
            description=description,
        )

        # Import here to avoid circular import (audits → schemas is fine;
        # schemas → audits is also fine since audits has no app deps)
        from apps.audits.services import AuditService
        AuditService.record(
            event_type=AuditEventType.SCHEMA_CREATED,
            schema_id=schema.id,
            metadata={"name": schema.name},
        )

        return schema

    @staticmethod
    def _assert_valid_meta_schema(schema_json: dict) -> None:
        try:
            jsonschema.Draft7Validator.check_schema(schema_json)
        except jsonschema.exceptions.SchemaError as exc:
            raise DomainValidationError(
                f"Provided schema_json is not a valid JSON Schema: {exc.message}"
            )
