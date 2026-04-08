from rest_framework import serializers
from apps.users.models import JiraUser, JiraRoleMapping
from common.constants import ConfigSphereRole


class JiraUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = JiraUser
        fields = [
            "id",
            "jira_account_id",
            "email",
            "display_name",
            "avatar_url",
            "jira_groups",
            "jira_project_roles",
            "configsphere_role",
            "role_override",
            "is_active",
            "last_synced_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "jira_account_id",
            "email",
            "display_name",
            "avatar_url",
            "jira_groups",
            "jira_project_roles",
            "last_synced_at",
            "created_at",
        ]


class RoleOverrideSerializer(serializers.Serializer):
    configsphere_role = serializers.ChoiceField(choices=ConfigSphereRole.CHOICES)
    role_override = serializers.BooleanField(default=True)


class JiraRoleMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = JiraRoleMapping
        fields = [
            "id",
            "jira_entity_type",
            "jira_entity_name",
            "configsphere_role",
            "priority",
        ]
