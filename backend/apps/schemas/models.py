from django.db import models


class SchemaDefinition(models.Model):
    """
    A named JSON Schema definition.

    Immutable after creation — changing a schema in place would silently
    invalidate previously-validated config versions.
    If a schema needs to evolve, create a new SchemaDefinition (future: versioned schemas).

    Fields:
        name        — human-readable label, must be unique
        schema_json — valid JSON Schema (Draft-7) object
        description — optional human notes
        created_at  — immutable creation timestamp
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, default="")
    schema_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"SchemaDefinition({self.name})"
