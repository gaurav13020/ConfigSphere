import logging
from datetime import datetime, timezone

from apps.users.models import JiraRoleMapping, JiraUser
from common.constants import ConfigSphereRole

logger = logging.getLogger(__name__)


class UserSyncService:
    """
    Creates or updates a JiraUser from Atlassian profile data.
    Computes the ConfigSphere role from JiraRoleMapping unless overridden.
    """

    def compute_role(
        self, jira_groups: list[str], jira_project_roles: list[str]
    ) -> str:
        """
        Evaluate active JiraRoleMapping rows (ordered by priority, ascending).
        First match wins.  Falls back to VIEWER if nothing matches.
        """
        mappings = JiraRoleMapping.objects.all()

        for mapping in mappings:
            if mapping.jira_entity_type == JiraRoleMapping.EntityType.GROUP:
                if mapping.jira_entity_name in jira_groups:
                    return mapping.configsphere_role
            elif mapping.jira_entity_type == JiraRoleMapping.EntityType.PROJECT_ROLE:
                if mapping.jira_entity_name in jira_project_roles:
                    return mapping.configsphere_role

        return ConfigSphereRole.VIEWER

    def sync_user(
        self,
        jira_profile: dict,
        jira_groups: list[str],
        jira_project_roles: list[str],
    ) -> JiraUser:
        """
        Upsert the JiraUser.  Role is re-computed from Jira membership data
        unless the user has role_override=True (set by an Admin).
        """
        account_id = jira_profile["accountId"]
        email = jira_profile.get("email", "")
        display_name = jira_profile.get("displayName", "")
        avatar_url = jira_profile.get("picture", "")

        user, created = JiraUser.objects.get_or_create(
            jira_account_id=account_id,
            defaults={
                "email": email,
                "display_name": display_name,
                "avatar_url": avatar_url,
                "jira_groups": jira_groups,
                "jira_project_roles": jira_project_roles,
                "configsphere_role": self.compute_role(jira_groups, jira_project_roles),
                "last_synced_at": datetime.now(tz=timezone.utc),
            },
        )

        if not created:
            user.email = email
            user.display_name = display_name
            user.avatar_url = avatar_url
            user.jira_groups = jira_groups
            user.jira_project_roles = jira_project_roles
            user.last_synced_at = datetime.now(tz=timezone.utc)

            if not user.role_override:
                user.configsphere_role = self.compute_role(
                    jira_groups, jira_project_roles
                )

            user.save()

        action = "created" if created else "updated"
        logger.info(
            "JiraUser %s (%s): role=%s", account_id, action, user.configsphere_role
        )
        return user
