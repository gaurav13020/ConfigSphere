from django.db import models
from common.constants import ConfigSphereRole


class JiraUser(models.Model):
    """
    Represents a user authenticated via Jira OAuth.
    Role is derived from their Jira groups/project roles and can be
    manually overridden by an Admin (role_override=True).
    """

    jira_account_id = models.CharField(max_length=255, unique=True, db_index=True)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=255)
    avatar_url = models.URLField(blank=True, default="")

    # Jira membership data — refreshed on every token refresh
    jira_groups = models.JSONField(default=list)         # ["configsphere-approvers", ...]
    jira_project_roles = models.JSONField(default=list)  # ["Developers", "Leads", ...]

    # ConfigSphere role derived from jira_groups / jira_project_roles
    configsphere_role = models.CharField(
        max_length=20,
        choices=ConfigSphereRole.CHOICES,
        default=ConfigSphereRole.VIEWER,
    )
    # When True, role will NOT be re-computed from Jira on token refresh.
    # Allows Admins to manually assign roles independent of Jira membership.
    role_override = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "jira_users"
        ordering = ["email"]

    def __str__(self):
        return f"{self.display_name} <{self.email}> [{self.configsphere_role}]"


class JiraRoleMapping(models.Model):
    """
    Admin-configurable mapping from a Jira group or project role to a
    ConfigSphere role.  Evaluated in ascending priority order; first match wins.
    """

    class EntityType(models.TextChoices):
        GROUP = "group", "Jira Group"
        PROJECT_ROLE = "project_role", "Jira Project Role"

    jira_entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    jira_entity_name = models.CharField(max_length=255)
    configsphere_role = models.CharField(
        max_length=20, choices=ConfigSphereRole.CHOICES
    )
    # Lower number = evaluated first.  Use this to resolve conflicts when a
    # user belongs to multiple mapped groups.
    priority = models.PositiveIntegerField(default=100)

    class Meta:
        db_table = "jira_role_mappings"
        unique_together = [("jira_entity_type", "jira_entity_name")]
        ordering = ["priority"]

    def __str__(self):
        return (
            f"{self.jira_entity_type}:{self.jira_entity_name} "
            f"→ {self.configsphere_role} (priority={self.priority})"
        )


class RefreshToken(models.Model):
    """
    Server-side refresh token record.  Storing tokens here allows revocation
    (logout, forced expiry, role-change invalidation).
    The actual value sent to the client is just the jti (UUID), set as an
    httpOnly cookie — the full token is never exposed.
    """

    jti = models.CharField(max_length=255, unique=True, db_index=True)
    jira_user = models.ForeignKey(
        JiraUser, on_delete=models.CASCADE, related_name="refresh_tokens"
    )
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "refresh_tokens"

    def __str__(self):
        status = "revoked" if self.revoked else "active"
        return f"RefreshToken({self.jira_user.email}, {status})"
