import base64
import logging
from datetime import datetime, timezone

import requests
from django.conf import settings

from apps.approvals.models import ApprovalRequest, ApprovalStatus
from apps.audits.services import AuditService
from apps.configs.models import ConfigVersion
from common.constants import AuditEventType, VersionStatus
from common.exceptions import ActivationError, ConflictError, NotFoundError

logger = logging.getLogger(__name__)


def _jira_auth_header() -> str:
    """Basic auth header for server-to-server Jira API calls using email + API token."""
    credentials = f"{settings.JIRA_EMAIL}:{settings.JIRA_API_TOKEN}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def _jira_headers() -> dict:
    return {
        "Authorization": _jira_auth_header(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _build_adf_description(version: ConfigVersion, notes: str) -> dict:
    """Build an Atlassian Document Format description for the Jira issue."""
    item = version.config_item
    scope_parts = [f"scope={item.scope_level}"]
    if item.region_name:
        scope_parts.append(f"region={item.region_name}")
    if item.group_name:
        scope_parts.append(f"group={item.group_name}")
    if item.service_name:
        scope_parts.append(f"service={item.service_name}")
    scope_str = ", ".join(scope_parts)

    paragraphs = [
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": f"Config key: {item.key}"}],
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": f"Scope: {scope_str}"}],
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": f"Version: #{version.version_number}"}],
        },
        {
            "type": "paragraph",
            "content": [{"type": "text", "text": f"Checksum: {version.checksum}"}],
        },
    ]

    if version.change_summary:
        paragraphs.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": f"Change summary: {version.change_summary}"}],
        })

    if notes:
        paragraphs.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": f"Submitter notes: {notes}"}],
        })

    return {"version": 1, "type": "doc", "content": paragraphs}


class ApprovalService:

    @staticmethod
    def submit(version_id: int, submitted_by: str, notes: str = "") -> ApprovalRequest:
        """
        Submit a VALIDATED config version for approval.
        Creates an ApprovalRequest and opens a Jira ticket.
        Raises ConflictError if an approval request already exists.
        """
        try:
            version = ConfigVersion.objects.select_related(
                "config_item", "config_item__schema"
            ).get(pk=version_id)
        except ConfigVersion.DoesNotExist:
            raise NotFoundError(f"ConfigVersion {version_id} does not exist.")

        if version.status != VersionStatus.VALIDATED:
            raise ConflictError(
                f"Only VALIDATED versions can be submitted for approval. "
                f"Current status: {version.status}."
            )

        if ApprovalRequest.objects.filter(config_version=version).exists():
            raise ConflictError("An approval request already exists for this version.")

        approval = ApprovalRequest.objects.create(
            config_version=version,
            submitted_by=submitted_by,
            submission_notes=notes,
            status=ApprovalStatus.PENDING,
        )

        # Create Jira ticket
        jira_issue_key, jira_issue_id, jira_issue_url = ApprovalService._create_jira_ticket(
            version, notes
        )
        if jira_issue_key:
            approval.jira_issue_key = jira_issue_key
            approval.jira_issue_id = jira_issue_id
            approval.jira_issue_url = jira_issue_url
            approval.save(update_fields=["jira_issue_key", "jira_issue_id", "jira_issue_url"])

        AuditService.record(
            event_type=AuditEventType.APPROVAL_SUBMITTED,
            actor=submitted_by,
            config_item_id=version.config_item_id,
            config_version_id=version.id,
            metadata={
                "version_number": version.version_number,
                "jira_issue_key": jira_issue_key,
                "notes": notes,
            },
        )

        return approval

    @staticmethod
    def _create_jira_ticket(version: ConfigVersion, notes: str) -> tuple[str, str, str]:
        """
        Opens a Jira issue for the approval request.
        Returns (issue_key, issue_id, issue_url) or ("", "", "") on failure.
        Failure is logged but not raised — approval request still persists.
        """
        item = version.config_item
        summary = (
            f"[ConfigSphere] Approve config change: "
            f"{item.key} @ {item.scope_level}"
        )

        payload = {
            "fields": {
                "project": {"key": settings.JIRA_PROJECT_KEY},
                "summary": summary,
                "description": _build_adf_description(version, notes),
                "issuetype": {"name": "Task"},
                "labels": ["configsphere", "config-approval"],
            }
        }

        try:
            resp = requests.post(
                f"{settings.JIRA_BASE_URL}/rest/api/3/issue",
                json=payload,
                headers=_jira_headers(),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            key = data["key"]
            issue_id = data["id"]
            url = f"{settings.JIRA_BASE_URL}/browse/{key}"
            logger.info("Created Jira issue %s for version %d", key, version.id)
            return key, issue_id, url
        except requests.RequestException as exc:
            logger.error("Failed to create Jira issue for version %d: %s", version.id, exc)
            return "", "", ""

    @staticmethod
    def approve(approval_id: int, reviewed_by: str, comment: str = "") -> ApprovalRequest:
        try:
            approval = ApprovalRequest.objects.select_related("config_version").get(
                pk=approval_id
            )
        except ApprovalRequest.DoesNotExist:
            raise NotFoundError(f"ApprovalRequest {approval_id} does not exist.")

        if approval.status != ApprovalStatus.PENDING:
            raise ConflictError(
                f"Approval request is already {approval.status}. Cannot approve."
            )

        approval.status = ApprovalStatus.APPROVED
        approval.reviewed_by = reviewed_by
        approval.review_comment = comment
        approval.reviewed_at = datetime.now(tz=timezone.utc)
        approval.save(update_fields=["status", "reviewed_by", "review_comment", "reviewed_at"])

        AuditService.record(
            event_type=AuditEventType.APPROVAL_APPROVED,
            actor=reviewed_by,
            config_item_id=approval.config_version.config_item_id,
            config_version_id=approval.config_version_id,
            metadata={
                "approval_id": approval.id,
                "jira_issue_key": approval.jira_issue_key,
                "comment": comment,
            },
        )
        return approval

    @staticmethod
    def reject(approval_id: int, reviewed_by: str, comment: str = "") -> ApprovalRequest:
        try:
            approval = ApprovalRequest.objects.select_related("config_version").get(
                pk=approval_id
            )
        except ApprovalRequest.DoesNotExist:
            raise NotFoundError(f"ApprovalRequest {approval_id} does not exist.")

        if approval.status != ApprovalStatus.PENDING:
            raise ConflictError(
                f"Approval request is already {approval.status}. Cannot reject."
            )

        approval.status = ApprovalStatus.REJECTED
        approval.reviewed_by = reviewed_by
        approval.review_comment = comment
        approval.reviewed_at = datetime.now(tz=timezone.utc)
        approval.save(update_fields=["status", "reviewed_by", "review_comment", "reviewed_at"])

        AuditService.record(
            event_type=AuditEventType.APPROVAL_REJECTED,
            actor=reviewed_by,
            config_item_id=approval.config_version.config_item_id,
            config_version_id=approval.config_version_id,
            metadata={
                "approval_id": approval.id,
                "jira_issue_key": approval.jira_issue_key,
                "comment": comment,
            },
        )
        return approval

    @staticmethod
    def process_jira_webhook(issue_id: str, new_status: str, reviewer: str = "jira-webhook") -> None:
        """
        Called by the Jira webhook receiver when an issue transitions.
        Finds the matching ApprovalRequest by jira_issue_id and approves or rejects it.
        """
        try:
            approval = ApprovalRequest.objects.get(
                jira_issue_id=issue_id,
                status=ApprovalStatus.PENDING,
            )
        except ApprovalRequest.DoesNotExist:
            logger.info("No pending approval for Jira issue %s — skipping.", issue_id)
            return

        approval_statuses = [s.lower() for s in settings.JIRA_APPROVAL_STATUSES]
        rejection_statuses = [s.lower() for s in settings.JIRA_REJECTION_STATUSES]
        normalized = new_status.lower()

        if normalized in approval_statuses:
            ApprovalService.approve(approval.id, reviewed_by=reviewer)
            logger.info("Auto-approved approval %d via Jira webhook (status=%s)", approval.id, new_status)
        elif normalized in rejection_statuses:
            ApprovalService.reject(approval.id, reviewed_by=reviewer)
            logger.info("Auto-rejected approval %d via Jira webhook (status=%s)", approval.id, new_status)
        else:
            logger.debug("Jira issue %s transitioned to '%s' — no action taken.", issue_id, new_status)
