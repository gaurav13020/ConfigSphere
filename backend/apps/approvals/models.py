from django.db import models
from apps.configs.models import ConfigVersion


class ApprovalStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

    CHOICES = [
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (REJECTED, "Rejected"),
    ]


class ApprovalRequest(models.Model):
    """
    Tracks the approval lifecycle for a ConfigVersion before it can be activated.
    One approval request per version (OneToOne). If an ApprovalRequest exists for
    a version, activation is blocked until status=APPROVED.
    """

    config_version = models.OneToOneField(
        ConfigVersion,
        on_delete=models.CASCADE,
        related_name="approval_request",
    )

    # Jira ticket details — populated after ticket is created
    jira_issue_key = models.CharField(max_length=50, blank=True, default="")   # e.g. CONFIGSPHERE-42
    jira_issue_id = models.CharField(max_length=50, blank=True, default="")    # internal Jira ID for webhook matching
    jira_issue_url = models.URLField(blank=True, default="")                   # browser link

    status = models.CharField(
        max_length=20,
        choices=ApprovalStatus.CHOICES,
        default=ApprovalStatus.PENDING,
        db_index=True,
    )

    submitted_by = models.CharField(max_length=255)   # email from JWT at submission time
    reviewed_by = models.CharField(max_length=255, blank=True, default="")
    submission_notes = models.TextField(blank=True, default="")
    review_comment = models.TextField(blank=True, default="")

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "approval_requests"

    def __str__(self):
        return f"ApprovalRequest(version={self.config_version_id}, {self.status})"
