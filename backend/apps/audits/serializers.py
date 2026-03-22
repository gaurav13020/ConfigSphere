from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "event_type",
            "actor",
            "config_item_id_ref",
            "config_version_id_ref",
            "schema_id_ref",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
