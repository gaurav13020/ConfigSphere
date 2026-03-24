from rest_framework import serializers

from .models import SchemaDefinition


class SchemaDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchemaDefinition
        fields = ["id", "name", "description", "schema_json", "created_at"]
        read_only_fields = ["id", "created_at"]


class SchemaDefinitionCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(default="", allow_blank=True)
    schema_json = serializers.JSONField()

    def validate_name(self, value):
        if SchemaDefinition.objects.filter(name=value).exists():
            raise serializers.ValidationError(
                f"A schema with name '{value}' already exists."
            )
        return value

    def validate_schema_json(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("schema_json must be a JSON object.")
        return value


class SchemaDefinitionUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(default="", allow_blank=True)
    schema_json = serializers.JSONField()

    def __init__(self, *args, schema_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.schema_id = schema_id

    def validate_name(self, value):
        # Allow the same name for the schema being updated, but not for other schemas
        existing = SchemaDefinition.objects.filter(name=value).exclude(id=self.schema_id)
        if existing.exists():
            raise serializers.ValidationError(
                f"A schema with name '{value}' already exists."
            )
        return value

    def validate_schema_json(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("schema_json must be a JSON object.")
        return value
