import jsonschema
import jsonschema.exceptions

from apps.schemas.models import SchemaDefinition
from common.exceptions import ValidationError as DomainValidationError


class SchemaValidationService:
    """
    Validates a config payload against a JSON Schema definition.

    Design decision:
      We return a (bool, error_message) tuple rather than raising, so the
      caller (ConfigVersionService) can decide whether to persist the draft
      with an error or raise. This makes the validation logic independently
      testable without side effects.
    """

    @staticmethod
    def validate(payload: dict, schema: SchemaDefinition) -> tuple[bool, str]:
        """
        Returns (True, "") on success, (False, error_description) on failure.
        Does not raise — callers decide what to do with failures.
        """
        validator = jsonschema.Draft7Validator(schema.schema_json)
        errors = list(validator.iter_errors(payload))

        if not errors:
            return True, ""

        # Collect all error messages for a complete picture
        messages = [f"{e.json_path}: {e.message}" for e in errors]
        return False, "; ".join(messages)

    @staticmethod
    def assert_valid(payload: dict, schema: SchemaDefinition) -> None:
        """
        Convenience method that raises DomainValidationError on failure.
        Use when you want hard rejection (e.g., in tests or future strict mode).
        """
        valid, error_message = SchemaValidationService.validate(payload, schema)
        if not valid:
            raise DomainValidationError(
                "Payload does not conform to schema.",
                details=[error_message],
            )
