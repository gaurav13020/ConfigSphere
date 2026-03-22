from rest_framework import serializers

from common.constants import ScopeLevel, VersionStatus
from .models import ConfigItem, ConfigVersion


# ── ConfigItem ───────────────────────────────────────────────────────────────

class ConfigItemSerializer(serializers.ModelSerializer):
    active_version_id = serializers.PrimaryKeyRelatedField(
        source="active_version", read_only=True
    )

    class Meta:
        model = ConfigItem
        fields = [
            "id",
            "key",
            "scope_level",
            "global_name",
            "region_name",
            "group_name",
            "service_name",
            "schema",
            "status",
            "active_version_id",
            "description",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "active_version_id"]


class ConfigItemCreateSerializer(serializers.Serializer):
    key = serializers.CharField(max_length=255)
    scope_level = serializers.ChoiceField(choices=ScopeLevel.CHOICES)
    global_name = serializers.CharField(max_length=255, default="default")
    region_name = serializers.CharField(max_length=255, required=False, allow_null=True, default=None)
    group_name = serializers.CharField(max_length=255, required=False, allow_null=True, default=None)
    service_name = serializers.CharField(max_length=255, required=False, allow_null=True, default=None)
    schema_id = serializers.IntegerField(required=False, allow_null=True, default=None)
    description = serializers.CharField(default="", allow_blank=True)
    created_by = serializers.CharField(required=False, allow_null=True, default=None)


# ── ConfigVersion ────────────────────────────────────────────────────────────

class ConfigVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigVersion
        fields = [
            "id",
            "config_item",
            "version_number",
            "payload",
            "checksum",
            "status",
            "validation_error",
            "change_summary",
            "created_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "version_number",
            "checksum",
            "status",
            "validation_error",
            "created_at",
        ]


class ConfigVersionCreateSerializer(serializers.Serializer):
    payload = serializers.JSONField()
    change_summary = serializers.CharField(default="", allow_blank=True)
    created_by = serializers.CharField(required=False, allow_null=True, default=None)

    def validate_payload(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("payload must be a JSON object (dict).")
        return value


# ── Resolved config ──────────────────────────────────────────────────────────

class ResolvedLayerSerializer(serializers.Serializer):
    scope_level = serializers.CharField()
    config_item_id = serializers.IntegerField()
    config_version_id = serializers.IntegerField()
    version_number = serializers.IntegerField()
    checksum = serializers.CharField()
    key = serializers.CharField()


class ResolvedConfigSerializer(serializers.Serializer):
    payload = serializers.DictField()
    checksum = serializers.CharField()
    layers = ResolvedLayerSerializer(many=True)
    scope_params = serializers.DictField()
